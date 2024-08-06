from dataclasses import dataclass


@dataclass
class Param:
    DataIndex: int = 0
    WeldingProcessName: str = "nan"
    WeldingMethod: str = "nan"
    WireDiameter: float = 0.0
    WeldingMaterial: str = ""
    WeldingShieldGas: str = "nan"
    ProcessingTypeCode: int = 0
    ParamName: str = ""
    ParamIndex: int = 0
    ParamValue: float = 0.0