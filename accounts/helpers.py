from accounts import models



def create_audit_log(user,action,instance=None,message="",changes=None):


    models.AuditLog.objects.create(user      = user,
                                   action    = action,
                                   model     = instance.__class__.__name__ if instance else "",
                                   object_id = str(instance.pk) if instance else "",
                                   message   = message,
                                   changes   = changes,
                                   )
    
