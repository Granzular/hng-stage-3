from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from main.serializers import ProfileSerializer
from main.models import Profile
from main.paginators import ProfilePagination
from main.utils import (natural_language_parser, fetch_external_apis_response,
                         validate_name, get_or_create_profile,
                         queryset_to_csv_response)
from rest_framework.permissions import IsAuthenticated


class ProfileViewSet(ModelViewSet):

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    http_method_names = ['head','get','post']
    pagination_class = ProfilePagination
    #permission_classes = [IsAuthenticated]

    def list(self,request,*args,**kwargs):
         q = request.query_params
         filters = {}
         # filters
         filters['gender'] = q.get('gender')
         filters['age_group'] = q.get('age_group')
         filters['country_id'] = q.get('country_id')
         filters['age__gte'] = q.get('min_age')
         filters['age__lte'] = q.get('max_age')
         filters['gender_probability__gte'] = q.get('min_gender_probability')
         filters['country_probability__gte'] = q.get('min_country_probability')
         # clean up filters for None values
         keys = filters.keys()
         filters = {key:filters[key] for key in keys if filters[key] != None}
         # sorting and order
         sort_by = q.get('sort_by')
         order = q.get('order') or 'asc' # asc => ascending.  desc => descending
         
         if sort_by =='age' or  sort_by == 'created_at' or sort_by == 'gender_probability':
            sort_by = sort_by if order=='asc' else '-' + sort_by
            queryset = Profile.objects.filter(**filters).order_by(sort_by)
         else:
            queryset = Profile.objects.filter(**filters)
        
         paginated_queryset = self.paginate_queryset(queryset) 
         serializer = ProfileSerializer(paginated_queryset,many=True)

         if q.get('format') == 'csv':
            # sends the response and a csv file
            # when ?format=csv
            return queryset_to_csv_response(queryset.values_list())

         return self.get_paginated_response(serializer.data)
         
    @action(methods=['get'],detail=False)
    def search(self,request,*args,**kwargs):
        q = request.query_params.get('q')
        if q == None:
            return Response({
                'status': 'error',
                'message': 'Missing or empty parameter'
            }, status=status.HTTP_400_BAD_REQUEST)

        filters = natural_language_parser(q)
        if filters.get('status') == 'error':
            code = filters.get('code')
            del filters['code']
            return Response(filters, status=code)

        queryset = Profile.objects.filter(**filters)
        if len(queryset) == 0:
            return Response({
                'status': 'error',
                'message': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = ProfileSerializer(paginated_queryset, many=True)

        return self.get_paginated_response(serializer.data)

    def create(self,request):
        # ADMIN access only
        name = request.data.get('name') or ''
        valid, response = validate_name(name)
        
        if valid == False:
            return response
        else:
            profile,is_new,error_message, is_error = get_or_create_profile(name)
            if is_error:
                return Response(error_message,status=status.HTTP_502_BAD_GATEWAY)
            elif is_new:
                 return Response({
                    "status":"success",
                    "data": {
                        "id":profile.id,
                        "name":profile.name,
                        "gender":profile.gender,
                        "gender_probability":profile.gender_probability,
                        #"sample_size":profile.sample_size,
                        "age":profile.age,
                        "age_group":profile.age_group,
                        "country_id":profile.country_id,
                        "country_name":profile.country_name,
                        "country_probability":profile.country_probability,
                        "created_at":profile.created_at
                    }}, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "status":"success",
                    "message":"Profile already exists",
                    "data": {
                        "id":profile.id,
                        "name":profile.name,
                        "gender":profile.gender,
                        "gender_probability":profile.gender_probability,
                        #"sample_size":profile.sample_size,
                        "age":profile.age,
                        "age_group":profile.age_group,
                        "country_id":profile.country_id,
                        "country_name":profile.country_name,
                        "country_probability":profile.country_probability,
                        "created_at":profile.created_at
                    }}, status=status.HTTP_200_OK)
