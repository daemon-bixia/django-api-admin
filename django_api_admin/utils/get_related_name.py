def get_related_name(fk):
    """
    Returns the name used to link the foreign key relationship.
    """
    if fk._related_name:
        return fk._related_name
    return fk.model._meta.model_name + '_set'
