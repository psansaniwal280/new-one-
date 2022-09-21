import math

"""Pagination function which will get the result ,page and limit and
 in return it will give the page data as a dict with flag True  
 if success or else if failed then it will return the flag as False with the message 
 that has to be raised  """


def locationPagination(result, page, limit):
    # flag = False
    if len(result) > 0:
        if page and limit:
            totalPosts = len(result)
            totalPages = math.ceil(len(result) / limit)
            if page <= totalPages and limit <= totalPosts:
                start = limit * (page - 1)
                result = result[start:start + limit]
                return {"result": result,
                        "page": page + 1 if page + 1 <= totalPages else None,
                        "limit": limit}

            elif page > totalPages :
                return {"result":None, "page":None,"limit":None}

            else:
                return {"result": result, "page": None, "limit": None}
        else:
            # flag = True
            return {"result": result, "page": None, "limit": None}
    else:
        # flag = True
        return {"result": result, "page": None, "limit": None}
