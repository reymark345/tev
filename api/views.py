from rest_framework.response import Response
from rest_framework.decorators import api_view
from main.models import (TevOutgoing)
from .serializers import ItemSerializer


@api_view(['GET'])
def getData(request, dv_no):
    items = TevOutgoing.objects.filter(dv_no=dv_no).values('dv_no', 'status_id')
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data)

