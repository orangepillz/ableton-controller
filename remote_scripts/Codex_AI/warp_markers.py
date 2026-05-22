"""WarpMarker mixins for the Codex_AI Ableton bridge."""

try:
    from .live_api import Live
except ImportError:
    from live_api import Live


class WarpMarkerMixin(object):
    def _add_warp_marker(self, clip, beat_time, sample_time):
        if sample_time is None:
            sample_time = self._sample_time_for_beat(clip, beat_time)
        last_error = None
        for marker in self._warp_marker_candidates(clip, beat_time, sample_time):
            try:
                clip.add_warp_marker(marker)
                return self._find_warp_marker(clip, beat_time)
            except Exception as error:
                last_error = error
        if last_error is None:
            raise ValueError("Live.Clip.WarpMarker is not available")
        raise ValueError("Could not add warp marker: %s" % last_error)

    def _sample_time_for_beat(self, clip, beat_time):
        target = float(beat_time)
        markers = sorted(self._warp_marker_infos(clip), key=lambda marker: float(marker.get("beat_time", 0.0)))
        usable = [marker for marker in markers if marker.get("beat_time") is not None and marker.get("sample_time") is not None]
        if len(usable) >= 2:
            left = usable[0]
            right = usable[1]
            for index in range(len(usable) - 1):
                current = usable[index]
                candidate = usable[index + 1]
                if float(current["beat_time"]) <= target <= float(candidate["beat_time"]):
                    left = current
                    right = candidate
                    break
                if target > float(candidate["beat_time"]):
                    left = current
                    right = candidate
            beat_span = float(right["beat_time"]) - float(left["beat_time"])
            if abs(beat_span) > 0.000001:
                ratio = (target - float(left["beat_time"])) / beat_span
                return float(left["sample_time"]) + ratio * (float(right["sample_time"]) - float(left["sample_time"]))
            return float(left["sample_time"])

        sample_rate = float(self._safe_get(clip, "sample_rate", 0.0) or 0.0)
        sample_length = float(self._safe_get(clip, "sample_length", 0.0) or 0.0)
        sample_duration = sample_length / sample_rate if sample_rate > 0.0 else 0.0
        clip_length = float(self._safe_get(clip, "length", 0.0) or 0.0)
        if clip_length <= 0.0:
            clip_length = float(self._safe_get(clip, "end_marker", 0.0) or 0.0)
        if clip_length <= 0.0:
            raise ValueError("Cannot infer sample_time for beat_time without warp markers or clip length")
        return max(0.0, min(sample_duration, (target / clip_length) * sample_duration))

    def _warp_marker_candidates(self, clip, beat_time, sample_time):
        classes = []
        if Live is not None:
            try:
                classes.append(Live.Clip.WarpMarker)
            except Exception:
                pass
        try:
            markers = list(clip.warp_markers)
            if markers:
                classes.append(type(markers[0]))
        except Exception:
            pass

        unique_classes = []
        for marker_class in classes:
            if marker_class not in unique_classes:
                unique_classes.append(marker_class)

        for marker_class in unique_classes:
            data = {"beat_time": float(beat_time)}
            if sample_time is not None:
                data["sample_time"] = float(sample_time)
            try:
                yield marker_class(**data)
            except Exception:
                pass
            if sample_time is not None:
                try:
                    yield marker_class(float(sample_time), float(beat_time))
                except Exception:
                    pass
            try:
                marker = marker_class()
                marker.beat_time = float(beat_time)
                if sample_time is not None:
                    marker.sample_time = float(sample_time)
                yield marker
            except Exception:
                pass
            if sample_time is not None:
                try:
                    yield marker_class(float(beat_time), float(sample_time))
                except Exception:
                    pass

    def _find_warp_marker(self, clip, beat_time):
        markers = self._warp_marker_infos(clip)
        if not markers:
            return None
        target = float(beat_time)
        best = min(markers, key=lambda marker: abs(float(marker.get("beat_time", 0.0)) - target))
        if abs(float(best.get("beat_time", 0.0)) - target) <= 0.01:
            return best
        return None

    def _warp_marker_infos(self, clip):
        if not self._safe_get(clip, "is_audio_clip", False):
            return []
        try:
            markers = list(clip.warp_markers)
        except Exception:
            return []
        return [self._warp_marker_info(marker) for marker in markers]

    def _warp_marker_info(self, marker):
        return {
            "sample_time": self._safe_get(marker, "sample_time"),
            "beat_time": self._safe_get(marker, "beat_time"),
        }
