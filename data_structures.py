from typing import Dict, List
from dataclasses import dataclass, asdict
import json


# ========== ДОПУСТИМЫЕ ЗНАЧЕНИЯ (для валидации) ==========

VALID_BUSINESS_TYPES = ["services", "software", "saas", "online_store"]
VALID_TAX_MODES = ["OSNO", "USN", "PATENT"]
VALID_INCOME_SOURCES = ["services", "subscription", "software_sales"]
VALID_TAX_SYSTEMS = ["USN_Income", "USN_Income_Minus_Expenses"]


# ========== КОЭФФИЦИЕНТЫ ДЛЯ РАСЧЁТОВ ==========

K_BUSINESS = {
    "services": 0.85,
    "software": 0.90,
    "saas": 0.70,
    "online_store": 1.20
}

K_REVENUE = {
    "services": 1.00,
    "subscription": 1.00,
    "software_sales": 0.90
}


# ========== КЛАСС ВХОДНЫХ ДАННЫХ ==========

@dataclass
class InputData:
    """Входные данные для расчёта окупаемости"""
    
    # Общие параметры
    project_name: str
    planning_years: int
    startup_capital: float
    
    # Выбираемые параметры
    business_type: str      # services, software, saas, online_store
    tax_mode: str           # OSNO, USN, PATENT
    income_source: str      # services, subscription, software_sales
    
    # Доходы
    monthly_customers_start: int
    customers_growth_monthly: float
    average_check: float
    additional_income_monthly: float
    
    # Персонал
    employees_count: int
    avg_salary: float
    has_benefit_employees: bool
    benefit_employees_count: int
    insurance_benefit_rate: float
    
    # Аренда и офис
    rent_monthly: float
    utilities_monthly: float
    office_expenses_monthly: float
    
    # Маркетинг
    marketing_budget_monthly: float
    
    # Прочие расходы
    cost_per_client_monthly: float
    other_fixed_expenses_monthly: float
    
    # Налоги
    tax_system: str          # USN_Income, USN_Income_Minus_Expenses
    tax_rate_usn_dr: float
    has_vat: bool
    insurance_rate_standard: float
    patent_cost: float
    
    # Дисконтирование
    discount_rate: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InputData':
        return cls(**data)
    
    @classmethod
    def from_json(cls, filepath: str) -> 'InputData':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def validate(self) -> List[str]:
        """Валидация данных"""
        errors = []
        
        if self.business_type not in VALID_BUSINESS_TYPES:
            errors.append(f"business_type должен быть из {VALID_BUSINESS_TYPES}")
        
        if self.tax_mode not in VALID_TAX_MODES:
            errors.append(f"tax_mode должен быть из {VALID_TAX_MODES}")
        
        if self.income_source not in VALID_INCOME_SOURCES:
            errors.append(f"income_source должен быть из {VALID_INCOME_SOURCES}")
        
        if self.tax_mode == "USN" and self.tax_system not in VALID_TAX_SYSTEMS:
            errors.append(f"Для УСН tax_system должен быть из {VALID_TAX_SYSTEMS}")
        
        if self.has_benefit_employees and self.benefit_employees_count > self.employees_count:
            errors.append("benefit_employees_count не может превышать employees_count")
        
        if self.planning_years <= 0:
            errors.append("planning_years должен быть > 0")
        
        if self.startup_capital <= 0:
            errors.append("startup_capital должен быть > 0")
        
        return errors
    
    def get_business_coefficient(self) -> float:
        return K_BUSINESS.get(self.business_type, 1.0)
    
    def get_revenue_coefficient(self) -> float:
        return K_REVENUE.get(self.income_source, 1.0)


# ========== КЛАССЫ ДЛЯ РЕЗУЛЬТАТОВ ==========

@dataclass
class ScenarioResult:
    """Результат расчёта для одного сценария"""
    npv: float
    irr: float
    pi: float
    pp: float
    cashflow: List[float]
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        pp = d.get("pp")
        pi = d.get("pi")
        if isinstance(pp, float) and (pp == float("inf") or pp != pp):
            d["pp"] = None
        if isinstance(pi, float) and (pi == float("inf") or pi != pi):
            d["pi"] = None
        return d


@dataclass
class FullResult:
    """Полный результат по трём сценариям"""
    scenarios: Dict[str, ScenarioResult]

    def to_dict(self) -> Dict:
        out = {}
        for name, r in self.scenarios.items():
            out[name] = r.to_dict() if r is not None else None
        return {"scenarios": out}

    def to_json(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)