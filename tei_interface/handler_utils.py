

def get_edit_index(form_data, error_category):
    """
    Retrieve and validate the edit index from submitted form data.

    Returns:
        int: The parsed edit index when editing an existing item.
        None: If no edit index was supplied.
        False: If the edit index is invalid. An error message is flashed using
            the supplied error category.

    Args:
        form_data (ImmutableMultiDict): Submitted form data containing an
            optional "edit_index" field.
        error_category (str): Flash message category to use if the edit index
            is invalid.
    """

    edit_index = form_data.get("edit_index")

    if edit_index in (None, "", "None"):
        return None

    try:
        return int(edit_index)
    except ValueError:
        flash("Invalid edit index.", error_category)
        return False


def success():
    """Return a successful handler response."""
    return {"ok": True, "error": None}



def failure(error=None):
    """Return a failed handler response."""
    return {"ok": False, "error": error}