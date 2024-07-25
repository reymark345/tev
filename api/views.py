from rest_framework.response import Response
from rest_framework.decorators import api_view
from main.models import (TevOutgoing,TevIncoming)
from .serializers import ItemSerializer, ItemSerializerStatus


@api_view(['GET'])
def getStatus(request, id_number):
    items = TevIncoming.objects.filter(id_no=id_number)
    serializer = ItemSerializerStatus(items, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getData(request, dv_no):
    items = TevOutgoing.objects.filter(dv_no=dv_no).values('dv_no', 'status_id')
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data)


# @api_view(['GET'])
# def getStatus(request, id_number):
#     items = TevIncoming.objects.filter(id_no=id_number)
#     serializer = ItemSerializerStatus(items, many=True)
#     print(serializer.data)
#     print("statussss")
#     return Response(serializer.data)


# @api_view(['GET'])
# def getData(request, dv_no):
#     items = TevOutgoing.objects.filter(dv_no=dv_no).values('dv_no', 'status_id')
#     serializer = ItemSerializer(items, many=True)
#     print(serializer.data)
#     print("getData")
#     return Response(serializer.data)


