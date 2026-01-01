from accounts import models



def create_audit_log(*,user,action,instance=None,message="",changes=None):
    if instance is not None and hasattr(instance,"pk"):
        model     = instance.__class__.__name__
        object_id = str(instance.pk)
    else:
        model = ""
        object_id = ""

    models.AuditLog.objects.create(user      = user,
                                   action    = action,
                                   model     = model,
                                   object_id = object_id,
                                   message   = message,
                                   changes   = changes,
                                   )
    
    