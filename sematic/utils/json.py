def fix_nan_inf(string: str) -> str:
    """
    Dirty hack to remedy mismatches between ECMAS6 JSON specs and Pythoh JSON
    specs Python respects the JSON5 spec (https://spec.json5.org/) which
    supports NaN, Infinity, and -Infinity as numbers, whereas ECMAS6 does not
    (Unexpected token N in JSON at position)
    """
    # TODO: find a more sustainable solution
    return (
        string.replace("NaN", '"NaN"')
        .replace("Infinity", '"Infinity"')
        .replace('-"Infinity"', '"-Infinity"')
    )
