from rest_framework.response import Response


def success_response(*,message,data,status_code):

    return Response({"status":True,
                     "message":message,
                     "data":data
                    },status=status_code
                   )




def error_response(*,message,data,status_code):
    
    return Response({"status":True,
                     "message":message,
                     "data":data,
                    },status=status_code
                   )