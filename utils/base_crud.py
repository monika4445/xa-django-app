from django.db.models import Q
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.filters import BaseFilterBackend

class GenericFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        search_fields = getattr(view, 'search_fields', [])
        filter_fields = getattr(view, 'filter_fields', [])
        search_param = request.query_params.get('search')
        filter_params = request.query_params.copy()
        filter_params.pop('search', None)

        if search_param:
            q = Q()
            for field in search_fields:
                q |= Q(**{f'{field}__icontains': search_param})
            queryset = queryset.filter(q)

        for field, value in filter_params.items():
            if field in filter_fields:
                queryset = queryset.filter(**{field: value})

        return queryset


class BaseCRUD(GenericViewSet):
    _model = None
    _serializer = None
    _serializer_update = None
    _serializer_create = None

    filter_backends = [GenericFilterBackend]
    search_fields = []

    def get(self, request, id):
        try:
            obj = self._model.objects.get(id=id)
        except:
            return Response({'response': 404, 'error': f'Not found this {id} obj'}, 404)

        serializer = self._serializer(obj)
        return Response(serializer.data, 200)

    def create(self, request):
        serializer = self._serializer_create(data=request.data)
        print(serializer)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, 200)
        else:
            return Response(serializer.errors, 400)

    def update(self, request, id):
        try:
            obj = self._model.objects.get(id=id)
        except:
            return Response({'response': 404, 'error': f'Not found this {id} obj'}, 404)

        serializer = self._serializer_update(data=request.data)
        if serializer.is_valid():
            serializer.instance = obj
            serializer.save()
            return Response(serializer.data, 200)
        else:
            return Response(serializer.errors, 400)

    def delete(self, request, id):
        try:
            obj = self._model.objects.get(id=id)
        except:
            return Response({'response': 404, 'error': f'Not found this {id} obj'}, 404)

        obj.delete()
        return Response({"response": 200}, 200)

    def lists(self, request):
        obj = self._model.objects.all()
        page = self.paginate_queryset(self.filter_queryset(obj))
        serializer = self._serializer(page, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data, 200)

    def get_queryset(self):
        return self._model.objects.all()
