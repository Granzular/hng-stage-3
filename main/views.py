from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from main.serializers import ProfileSerializer
from main.models import Profile
from main.paginators import ProfilePagination
from main.utils import natural_language_parser



class ProfileViewSet(ModelViewSet):

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    http_method_names = ['head','get']
    pagination_class = ProfilePagination

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