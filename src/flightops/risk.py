from flightops.domain import (
    AssessmentStatus,
    ConstraintResult,
    MissionResult,
    OperationalLimits,
    SegmentResult,
    WeatherCondition,
)

RULE_VERSION = "2026-01"
WARNING_RATIO = 0.8
_SEVERITY = {
    AssessmentStatus.SAFE: 0,
    AssessmentStatus.WARNING: 1,
    AssessmentStatus.UNSAFE: 2,
}


def _maximum_constraint(metric: str, value: float | None, limit: float) -> ConstraintResult:
    if value is None:
        return ConstraintResult(
            metric,
            AssessmentStatus.UNSAFE,
            None,
            limit,
            None,
            f"{metric} forecast is missing",
        )
    margin = limit - value
    if value > limit:
        status = AssessmentStatus.UNSAFE
        reason = f"{metric} exceeds the configured maximum"
    elif limit == 0 or value >= limit * WARNING_RATIO:
        status = AssessmentStatus.WARNING
        reason = f"{metric} is within 20% of the configured maximum"
    else:
        status = AssessmentStatus.SAFE
        reason = f"{metric} is within the configured limit"
    return ConstraintResult(metric, status, value, limit, margin, reason)


def _temperature_constraint(
    value: float | None, minimum: float, maximum: float
) -> ConstraintResult:
    limit = f"{minimum}..{maximum}"
    if value is None:
        return ConstraintResult(
            "temperature",
            AssessmentStatus.UNSAFE,
            None,
            limit,
            None,
            "temperature forecast is missing",
        )
    if value < minimum or value > maximum:
        return ConstraintResult(
            "temperature",
            AssessmentStatus.UNSAFE,
            value,
            limit,
            -min(abs(value - minimum), abs(value - maximum)),
            "temperature is outside the configured range",
        )
    span = maximum - minimum
    margin = min(value - minimum, maximum - value)
    if margin <= span * (1 - WARNING_RATIO):
        status = AssessmentStatus.WARNING
        reason = "temperature is near a configured boundary"
    else:
        status = AssessmentStatus.SAFE
        reason = "temperature is within the configured range"
    return ConstraintResult("temperature", status, value, limit, margin, reason)


def evaluate_condition(
    condition: WeatherCondition, limits: OperationalLimits, segment_index: int
) -> SegmentResult:
    constraints = (
        _maximum_constraint("wind_speed", condition.wind_speed_mps, limits.max_wind_speed_mps),
        _maximum_constraint("wind_gust", condition.wind_gust_mps, limits.max_gust_speed_mps),
        _maximum_constraint(
            "precipitation",
            condition.precipitation_mm_per_hour,
            limits.max_precipitation_mm_per_hour,
        ),
        _temperature_constraint(
            condition.temperature_c,
            limits.min_temperature_c,
            limits.max_temperature_c,
        ),
    )
    status = max((item.status for item in constraints), key=_SEVERITY.__getitem__)
    return SegmentResult(segment_index, status, constraints)


def evaluate_mission(
    conditions: list[WeatherCondition], limits: OperationalLimits
) -> MissionResult:
    segments = tuple(
        evaluate_condition(condition, limits, index) for index, condition in enumerate(conditions)
    )
    if not segments:
        raise ValueError("At least one segment condition is required")
    status = max((segment.status for segment in segments), key=_SEVERITY.__getitem__)
    candidates = [
        constraint
        for segment in segments
        for constraint in segment.constraints
        if constraint.status == status
    ]
    limiting = min(
        candidates,
        key=lambda item: (
            float("inf") if item.margin is None else item.margin,
            item.metric,
        ),
    )
    return MissionResult(status, limiting.metric, segments)


def serialize_result(result: MissionResult) -> dict[str, object]:
    return {
        "status": result.status.value,
        "limiting_factor": result.limiting_factor,
        "rule_version": RULE_VERSION,
        "segments": [
            {
                "segment_index": segment.segment_index,
                "status": segment.status.value,
                "constraints": [
                    {
                        "metric": item.metric,
                        "status": item.status.value,
                        "value": item.value,
                        "limit": item.limit,
                        "margin": item.margin,
                        "reason": item.reason,
                    }
                    for item in segment.constraints
                ],
            }
            for segment in result.segments
        ],
    }
