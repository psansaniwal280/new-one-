import math

"""Pagination function which will get the result ,page and limit and
 in return it will give the page data as a dict with flag True  
 if success or else if failed then it will return the flag as False with the message 
 that has to be raised  """


def pagination(result, page, limit):
    flag = False
    if result:
        if len(result) > 0:
            if page and limit:
                if limit > len(result):
                    flag = True
                    return flag, {"result": result, "total_pages": None, "page": None, "limit": None}
                totalPages = math.ceil(len(result) / limit)
                if page <= totalPages:
                    start = limit * (page - 1)
                    result = result[start:start + limit]
                    flag = True
                    return flag, {"result": result,
                                  "total_pages": totalPages,
                                  "page": page + 1 if page+1 <= totalPages else None,
                                  "limit": limit}
                else:
                    return flag, "invalid request; page provided exceeded total"
            elif page == limit is None:
                flag = True
                return flag, {"result": result, "total_pages": None, "page": None, "limit": None}
            elif page is None and limit is not None:
                return flag, "invalid request; limit cannot be provided without page"
            elif limit is None and page is not None:
                return flag, "invalid request; page cannot be provided without limit"
        else:
            flag = True
            return flag, {"result": result, "total_pages": None, "page": None, "limit": None}
    else:
        flag = True
        return flag, {"result": result, "total_pages": None, "page": None, "limit": None}
