from rest_framework.response import Response
from rest_framework.decorators import api_view
from main.models import (TevOutgoing,TevIncoming)
from .serializers import ItemSerializer, ItemSerializerStatus
from django.db import connection

# @api_view(['GET'])
# def getStatus(request, id_number):
#     items = TevIncoming.objects.filter(id_no=id_number)
#     serializer = ItemSerializerStatus(items, many=True)
#     return Response(serializer.data)

@api_view(['GET'])
def getStatus(request, id_number):
    sql_query = """
    SELECT 
        ti.id, 
        ti.code, 
        ti.id_no,
        ti.original_amount, 
        ti.final_amount, 
        st.name AS status, 
        GROUP_CONCAT(tb.purpose SEPARATOR ', ') AS purposes,
        ti.incoming_in,
        ti.incoming_out,
        CONCAT_WS(' ', ui.first_name, ui.last_name) AS incoming_by,
        ti.date_payrolled,
        CONCAT_WS(' ', pb.first_name, pb.last_name) AS payrolled_by,
        t_o.dv_no, 
        t_o.box_b_out,
        t_o.otg_d_received,
        CONCAT_WS(' ', ot_r.first_name, ot_r.last_name) AS otg_r_user_id,
        t_o.otg_d_forwarded,
        CONCAT_WS(' ', ot_f.first_name, ot_f.last_name) AS otg_out_user_id,
        t_o.b_d_received,
        CONCAT_WS(' ', b_r.first_name, b_r.last_name) AS b_r_user_id,
        t_o.b_d_forwarded,
        CONCAT_WS(' ', b_f.first_name, b_f.last_name) AS b_out_user_id,
        t_o.j_d_received,
        CONCAT_WS(' ', j_r.first_name, j_r.last_name) AS j_r_user_id,
        t_o.j_d_forwarded,
        CONCAT_WS(' ', j_f.first_name, j_f.last_name) AS j_out_user_id,
        t_o.a_d_received,
        CONCAT_WS(' ', a_r.first_name, a_r.last_name) AS a_r_user_id,
        t_o.a_d_forwarded,
        CONCAT_WS(' ', a_f.first_name, a_f.last_name) AS a_out_user_id,
        CONCAT_WS(' ', ob.first_name, ob.last_name) AS out_by,
        ch.name AS charges, 
        cl.name AS cluster,
        GROUP_CONCAT(t3.name SEPARATOR ', ') AS remarks,
        CONCAT_WS(' ', au.first_name, au.last_name) AS forwarded_by,
        CONCAT_WS(' ', rb.first_name, rb.last_name) AS reviewed_by,
        ti.date_reviewed
    FROM 
        tev_incoming AS ti 
    LEFT JOIN 
        tev_bridge AS tb ON tb.tev_incoming_id = ti.id
    LEFT JOIN 
        status AS st ON st.id = ti.status_id
    LEFT JOIN 
        tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
    LEFT JOIN 
        charges AS ch ON ch.id = tb.charges_id
    LEFT JOIN 
        cluster AS cl ON cl.id = t_o.cluster
    LEFT JOIN 
        auth_user AS ob ON ob.id = t_o.out_by
    LEFT JOIN 
        remarks_r AS t2 ON t2.incoming_id = ti.id
    LEFT JOIN 
        remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
    LEFT JOIN 
        auth_user AS au ON au.id = ti.forwarded_by
    LEFT JOIN 
        auth_user AS rb ON rb.id = ti.reviewed_by
    LEFT JOIN 
        auth_user AS ui ON ui.id = ti.user_id
    LEFT JOIN 
        auth_user AS pb ON pb.id = ti.payrolled_by
    LEFT JOIN 
        auth_user AS ot_r ON ot_r.id = t_o.otg_r_user_id
    LEFT JOIN 
        auth_user AS ot_f ON ot_f.id = t_o.otg_out_user_id
    LEFT JOIN 
        auth_user AS b_r ON b_r.id = t_o.b_r_user_id
    LEFT JOIN 
        auth_user AS b_f ON b_f.id = t_o.b_out_user_id
    LEFT JOIN 
        auth_user AS j_r ON j_r.id = t_o.j_r_user_id
    LEFT JOIN 
        auth_user AS j_f ON j_f.id = t_o.j_out_user_id
    LEFT JOIN 
        auth_user AS a_r ON a_r.id = t_o.a_r_user_id
    LEFT JOIN 
        auth_user AS a_f ON a_f.id = t_o.a_out_user_id
    WHERE 
        ti.id_no = %s
    GROUP BY 
        ti.id, 
        ti.code, 
        ti.id_no,
        ti.original_amount, 
        ti.final_amount, 
        ti.status_id, 
        ti.remarks, 
        ti.incoming_in,
        ti.incoming_out,
        ti.date_payrolled,
        ti.payrolled_by,
        t_o.dv_no,
        t_o.box_b_out,
        t_o.otg_d_received,
        t_o.otg_r_user_id,
        t_o.otg_d_forwarded, 
        t_o.otg_out_user_id,
        t_o.b_d_received,
        t_o.b_r_user_id,
        t_o.b_d_forwarded,
        t_o.b_out_user_id,
        t_o.j_d_received,
        t_o.j_r_user_id,
        t_o.j_d_forwarded,
        t_o.j_out_user_id,
        t_o.a_d_received,
        t_o.a_r_user_id,
        t_o.a_d_forwarded,
        t_o.a_out_user_id,
        t_o.out_by,
        ch.name, 
        cl.name
    ORDER BY 
        ti.id DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_query, [id_number])
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
    mapped_data = [
        dict(zip(columns, row)) for row in rows
    ]
    serializer = ItemSerializerStatus(mapped_data, many=True)
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


