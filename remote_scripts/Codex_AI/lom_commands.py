"""LomCommand mixins for the Codex_AI Ableton bridge."""


class LomCommandMixin(object):
    def _lom_set(self, payload):
        path = payload.get("path")
        value = payload.get("value")
        target_path, attribute = self._split_lom_attribute(path)
        target = self._resolve_lom_path(target_path)
        current = getattr(target, attribute)
        coerced = self._coerce_like(value, current)
        setattr(target, attribute, coerced)
        return {"path": path, "value": self._serialize(getattr(target, attribute))}

    def _lom_call(self, payload):
        method = self._resolve_lom_path(payload.get("path"))
        if not callable(method):
            raise ValueError("LOM path is not callable: %r" % (payload.get("path"),))
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        if not isinstance(args, list):
            raise ValueError("args must be a list")
        if not isinstance(kwargs, dict):
            raise ValueError("kwargs must be an object")
        return self._serialize(method(*args, **kwargs))

    def _lom_inspect(self, payload):
        obj = self._resolve_lom_path(payload.get("path"))
        attrs = []
        methods = []
        for name in dir(obj):
            if name.startswith("_"):
                continue
            try:
                value = getattr(obj, name)
            except Exception:
                continue
            if callable(value):
                methods.append(name)
            else:
                attrs.append({"name": name, "summary": self._summary(value)})
        return {
            "path": payload.get("path"),
            "type": type(obj).__name__,
            "summary": self._summary(obj),
            "attributes": attrs,
            "methods": methods,
        }
