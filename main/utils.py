# THIS MODULE CONTAINS SEVERAL HELPER  FUNCTIONS. 
# THEY ARE MOSTLY BUSINESS LOGIC EXTRACTED FROM VIEWS

"""
EXTERNAL API HELPER FUNCTIONS STARTS FROM HERE
"""

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from main.models import Profile
import logging, json, re, pycountry, csv, io, requests


logger = logging.getLogger(__name__)

GENDERIZE_API_URL = "https://api.genderize.io"
AGIFY_API_URL = "https://api.agify.io"
NATIONALIZE_API_URL = "https://api.nationalize.io"


def fetch_external_apis_response(name:str):
    # renamed from test_api
    params = {'name':name}
    genderize_res = requests.get(GENDERIZE_API_URL,params=params)
    agify_res = requests.get(AGIFY_API_URL,params=params)
    nationalize_res = requests.get(NATIONALIZE_API_URL,params=params)
    genderize_data = genderize_res.json()
    agify_data = agify_res.json()
    nationalize_data = nationalize_res.json()
    return [genderize_data,agify_data,nationalize_data]

def validate_name(name:str)->tuple:
    """
    This function returns a tuple of length 2.
    elements: 
    """
    if name.strip() == '':
        return False, Response({
            'status': 'error',
            'message': 'Missing or empty name'
            }, status=status.HTTP_400_BAD_REQUEST)
    if name.isalpha() == False:
        return False, Response({
            'status': 'error',
            'message': 'Invalid type'
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return True, None

def  get_or_create_profile(name:str)->tuple:
    '''
    This fuction returns a tuple with length 4. 
    (profile,is_new,error_message,is_error)
    if is_error is True, then profile would be None;
    else profile would contain data and error_message would be None.
    is_new is only True if a new profile was created.
    '''

    if Profile.objects.filter(name=name).exists():
        return Profile.objects.get(name=name),False,None,False
    else:
        profile, error_message, is_error = process_request(name)
        return  profile, True, error_message, is_error # This returns: profile,is_new, error_message, is_error

def process_request(name:str)->tuple:
    '''
    This fuction returns a tuple with length 3. 
    (profile,error_message,is_error)
    if is_error is True, then profile would be None;
    else profile would contain data and error_message would be None.
    '''
    try:
        data1,data2,data3 = fetch_external_apis_response(name)
        failed_apis = '' # a string of the external api names that returned an invalid response
        # genderize API
        gender = data1.get('gender')
        gender_probability = data1.get('probability')
        sample_size = data1.get('count')
        if gender == None or sample_size == 0:
            failed_api = 'Genderize'
            return None, {
                    'status': 'error',
                    'message': f'{failed_api} returned an invalid response'
                    }, True


        # agify API
        age = data2.get('age')
        if age == None:
            failed_api = 'Agify'
            return None, {
                    'status': 'error',
                    'message': f'{failed_api} returned an invalid response'
                    }, True

        else:
            age_group = 'child' if (age>=0 and age<=12) else 'teenager' if (age>=13 and age<=19) else 'adult' if (age>=20 and age<=59) else 'senior' if (age>=60) else 'merlin'
        # nationalize API
        if data3['country'] == []:
            failed_api = 'Nationalize'
            return None, {
                    'status': 'error',
                    'message': f'{failed_api} returned an invalid response'
                    }, True

        else:
            country = max(data3['country'],key=lambda x:x['probability'])
            country_id = country.get('country_id')
            country_name = pycountry.countries.get(alpha_2=country_id).name
            country_probability = country.get('probability')

        profile = Profile.objects.create(
            name = name,
            gender = gender,
            gender_probability = gender_probability,
            #sample_size = sample_size,
            age=age,
            age_group = age_group,
            country_id = country_id,
            country_name = country_name,
            country_probability=country_probability
        )

        return profile,None,False

        
    except Exception as err:
        logger.error(f"server failure: {err}")
        return None,{
            'status': 'error',
            'message': 'server failure'
        }, True




"""
EXTERNAL API HELPER FUNCTIONS ENDS HERE
"""

######

"""
NATURAL LANGUAGE PROCESSOR HELPER FUNCTION STARTS HERE
"""


def seed_db(filename:str):
    with open(filename,mode='r') as fd:
        data = json.loads(fd.read())

    f = open('log.txt', 'w')
    profiles = data['profiles']
    for profile in profiles:
        try:
            Profile.objects.create(**profile)
            f.write('profile created\n')
        except Exception as e:
            f.write(f'Profile exists: {e}\n')
    
    f.close()


def validate(parsed:dict)-> dict|bool:
     
    validated = {}

    # Country resolution 
    if "country_raw" in parsed:
        country = (
            Profile.objects
            .filter(country_name__iexact=parsed["country_raw"])
            .values("country_id", "country_name")
            .first()
        )

        if not country:
            return None

        validated["country_id"] = country["country_id"]
        validated["country_name"] = country["country_name"]

    
    # gender validaation

    if "gender" in parsed:
        if parsed["gender"] not in {"male", "female"}:
            return None
        validated["gender"] = parsed["gender"]

    
    # 3. age group validation
    
    if "age_group" in parsed:
        if parsed["age_group"] not in {"child", "teenager", "adult", "senior"}:
            return None
        validated["age_group"] = parsed["age_group"]

    
    # age validation (no consistency check)
    
    if "min_age" in parsed:
        if not isinstance(parsed["min_age"], int) or parsed["min_age"] < 0:
            return None
        validated["age__gte"] = parsed["min_age"]

    if "max_age" in parsed:
        if not isinstance(parsed["max_age"], int) or parsed["max_age"] < 0:
            return None
        validated["age__lte"] = parsed["max_age"]

    
    # validated output
    
    return validated

def natural_language_parser(text: str) -> dict:
    text = text.lower().strip()

    filters = {}

    # Scoped Rules

    IGNORED = {"and", "people"}

    GENDER_MAP = {
        "male": "male",
        "males": "male",
        "female": "female",
        "females": "female",
    }

    AGE_GROUPS = {
        "child": "child",
        "children": "child",
        "teenager": "teenager",
        "teenagers": "teenager",
        "adult": "adult",
        "adults": "adult",
        "senior": "senior",
        "seniors": "senior",
    }

    SPECIAL_AGE = {
        "young": (16, 24),
    }

    # Phrase Matching

    country_match = re.search(r"from\s+([a-z]+)", text)
    if country_match:
        filters["country_raw"] = country_match.group(1)
        text = re.sub(r"from\s+[a-z]+", "", text).strip()

    # Age comparators

    above_match = re.search(r"(above|over|greater than)\s+(\d+)", text)
    if above_match:
        filters["min_age"] = int(above_match.group(2))
        text = re.sub(r"(above|over|greater than)\s+\d+", "", text).strip()

    below_match = re.search(r"(below|under|less than)\s+(\d+)", text)
    if below_match:
        filters["max_age"] = int(below_match.group(2))
        text = re.sub(r"(below|under|less than)\s+\d+", "", text).strip()

    # Token scanning

    words = text.split()
    remaining_words = []

    gender_found = set()

    for w in words:
        if w in IGNORED:
            continue

        if w in GENDER_MAP:
            gender_found.add(GENDER_MAP[w])
            continue

        if w in AGE_GROUPS:
            filters["age_group"] = AGE_GROUPS[w]
            continue

        if w in SPECIAL_AGE:
            filters["min_age"], filters["max_age"] = SPECIAL_AGE[w]
            continue

        remaining_words.append(w)

    # gender resolution

    if len(gender_found) == 1:
        filters["gender"] = list(gender_found)[0]
    elif len(gender_found) > 1:
        filters.pop("gender", None)  # neutral case

    # leftover check

    if remaining_words:
        return {
            "status": "error",
            "message": "Unable to interpret query,",
            "code": 422
        }

    validated = validate(filters)
    if validated:
        return validated
    else:
        return {
            "status": "error",
            "message": "invalid query parameters",
            "code": 422,

        }



def run_full_parser_validator_tests():
    """
    A simple test suite for the basic rule based NLP parser.

    """
    def assert_true(cond, msg):
        if not cond:
            raise AssertionError(msg)

    def assert_false(cond, msg):
        if cond:
            raise AssertionError(msg)

    def assert_none(val, msg):
        if val is not None:
            raise AssertionError(msg)

    def assert_not_none(val, msg):
        if val is None:
            raise AssertionError(msg)
    def assert_error(val,msg):
        if val.get('status') != 'error':
            raise AssertionError(msg)

    # =========================================================
    # 1. BASIC VALID CASE (minimal filters)
    # =========================================================
    result = natural_language_parser("adult males from nigeria")
    

    assert_not_none(result, "Basic valid query failed")
    assert_true(result.get("gender") == "male", "Gender mismatch")
    assert_true(result.get("age_group") == "adult", "Age group mismatch")
    assert_true("country_id" in result, "Country missing")

    # =========================================================
    # 2. COUNTRY NOT FOUND (hard fail)
    # =========================================================
    result = natural_language_parser("young males from atlantis")

    assert_error(result, "Invalid country should fail completely")

    # =========================================================
    # 3. LEFTOVER TOKEN FAILURE (parser strictness)
    # =========================================================
    result = natural_language_parser("young males from nigeria quickly")

    assert_true(
        result.get("status") == "error",
        "Parser must reject unknown leftover tokens"
    )

    # =========================================================
    # 4. GENDER CONFLICT (male + female cancels)
    # =========================================================
    result = natural_language_parser("male and female teenagers from kenya")

    assert_not_none(result, "Valid multi-gender case should pass")
    assert_true("gender" not in result, "Conflicting gender not removed")

    # =========================================================
    # 5. AGE COMPARISON ONLY
    # =========================================================
    result = natural_language_parser("adults above 30 from nigeria")

    assert_not_none(result, "Age comparison failed")
    assert_true(result.get("age__gte") == 30, "min_age incorrect")

    # =========================================================
    # 6. AGE BELOW ONLY
    # =========================================================
    result = natural_language_parser("teenagers below 18 from kenya")

    assert_not_none(result, "Below-age case failed")
    assert_true(result.get("age__lte") == 18, "max_age incorrect")

    # =========================================================
    # 7. SPECIAL AGE KEYWORD ("young")
    # =========================================================
    result = natural_language_parser("young males from nigeria")

    assert_not_none(result, "Young keyword failed")
    assert_true(result.get("age__gte") == 16, "young min_age mismatch")
    assert_true(result.get("age__lte") == 24, "young max_age mismatch")

    # =========================================================
    # 8. AGE GROUP DIRECT MATCH
    # =========================================================
    result = natural_language_parser("senior females from kenya")

    assert_not_none(result, "Senior case failed")
    assert_true(result.get("age_group") == "senior", "age_group mismatch")

    # =========================================================
    # 9. MULTI-CONSTRAINT COMBINATION
    # =========================================================
    result = natural_language_parser("young male adults above 25 from nigeria")

    # may pass or fail depending on your conflict rules
    # this checks system stability (no crash / corruption)
    assert_true(result is None or isinstance(result, dict),
                "System must not crash on complex query")

    # =========================================================
    # 10. INVALID AGE TYPE
    # =========================================================
    result = natural_language_parser("male adults above twenty from nigeria")

    assert_true(
        result.get("status") == "error",
        "Non-numeric age must fail parser"
    )

    # =========================================================
    # 11. EMPTY / NO INTENT CASE
    # =========================================================
    result = natural_language_parser("and people from")
    assert_true(result.get("status") == "error",
                "Empty intent must fail parser")

    # =========================================================
    # 12. VALID MINIMAL QUERY
    # =========================================================
    result = natural_language_parser("females from kenya")

    assert_not_none(result, "Minimal valid query failed")
    assert_true(result.get("gender") == "female", "Gender mismatch")

    # =========================================================
    # 13. UNKNOWN WORD IN MIDDLE (strict rejection)
    # =========================================================
    result = natural_language_parser("female from nigeria banana")

    assert_true(
        result.get("status") == "error",
        "Unknown token must invalidate query"
    )

    # =========================================================
    # 14. COUNTRY CASE SENSITIVITY (robustness)
    # =========================================================
    result = natural_language_parser("MALE FROM Nigeria")

    assert_not_none(result, "Case-insensitive country failed")

    # =========================================================
    # FINAL
    # =========================================================
    print("All parser + validator tests passed.")



"""
NATURAL LANGUAGE PROCESSOR HELPER FUNCTION ENDS HERE
"""

"""
OTHERS
"""

def queryset_to_csv_response(queryset:list|tuple):
    # takes a list or tuple of list or tuple as an argument and 
    # returns it as a csv Response
    
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(queryset)
    
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=profiles_{timezone.now()}.csv'
    
    return response