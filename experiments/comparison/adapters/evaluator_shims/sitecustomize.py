from __future__ import annotations

try:
    import shapely
except Exception:  # pragma: no cover - only active inside evaluator subprocesses.
    shapely = None


if shapely is not None:
    _original_equals_exact = getattr(shapely, "equals_exact", None)
    _normalize = getattr(shapely, "normalize", None)

    if _original_equals_exact is not None:

        def _equals_exact_compat(a, b, tolerance=0.0, **kwargs):
            normalize = bool(kwargs.pop("normalize", False))
            if normalize and _normalize is not None:
                try:
                    a = _normalize(a)
                    b = _normalize(b)
                except Exception:
                    pass
            return _original_equals_exact(a, b, tolerance=tolerance, **kwargs)

        shapely.equals_exact = _equals_exact_compat


try:
    import geopandas as gpd
except Exception:  # pragma: no cover - only active inside evaluator subprocesses.
    gpd = None


if gpd is not None:

    def _union_all_compat(self):
        return self.unary_union

    for _klass_name in ("GeoSeries", "GeoDataFrame"):
        _klass = getattr(gpd, _klass_name, None)
        if _klass is not None and not hasattr(_klass, "union_all"):
            setattr(_klass, "union_all", _union_all_compat)
