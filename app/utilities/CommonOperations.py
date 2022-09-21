

def default_get_or_none(classModel, **kwargs):
    try:
        return classModel.objects.using('default').get(**kwargs)
    # except classModel.MultipleObjectsReturned as e:
    #     print('ERR====>', e)
    except classModel.DoesNotExist:
        return None
