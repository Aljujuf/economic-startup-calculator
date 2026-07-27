"""
Главный модуль - оркестратор
"""

import json
from typing import Dict, Union

from data_structures import InputData, FullResult, ScenarioResult
from formulas_and_calculations import (
    generate_cashflow_series,
    aggregate_yearly_cashflow,
    calculate_npv,
    calculate_pi,
    calculate_payback_period
)
from algorithms import calculate_irr
from scenarios import get_scenario_modifiers, get_all_scenarios


class StartupValuationOrchestrator:
    def __init__(self, input_data: Union[Dict, InputData]):
        if isinstance(input_data, dict):
            self.input_data = InputData.from_dict(input_data)
        else:
            self.input_data = input_data
        
        errors = self.input_data.validate()
        if errors:
            raise ValueError(f"Ошибки валидации: {', '.join(errors)}")
    
    def analyze_scenario(self, name: str) -> ScenarioResult:
        modifiers = get_scenario_modifiers(name)
        
        monthly = generate_cashflow_series(self.input_data, modifiers)
        yearly = aggregate_yearly_cashflow(monthly)
        
        rate = self.input_data.discount_rate
        if modifiers and 'discount_rate' in modifiers:
            rate = self.input_data.discount_rate + modifiers['discount_rate']
        
        npv = calculate_npv(yearly, rate)
        irr = calculate_irr(yearly)
        pp = calculate_payback_period(yearly)
        pi = calculate_pi(yearly, npv)
        
        return ScenarioResult(npv=npv, irr=irr, pi=pi, pp=pp, cashflow=yearly)
    
    def run_full_analysis(self) -> FullResult:
        results = {}
        for name in get_all_scenarios():
            try:
                results[name] = self.analyze_scenario(name)
            except Exception as e:
                print(f" {name} - {e}")
                results[name] = None
        return FullResult(scenarios=results)


def process_request(input_json: Dict) -> Dict:
    """Основная функция для API"""
    orchestrator = StartupValuationOrchestrator(input_json)
    result = orchestrator.run_full_analysis()
    return result.to_dict()


# Пример использования (для теста)
if __name__ == "__main__":
    test_data = {
        "project_name": "project",
        "planning_years": 5,
        "startup_capital": 5000000,
        "business_type": "saas",
        "tax_mode": "USN",
        "income_source": "subscription",
        "monthly_customers_start": 100,
        "customers_growth_monthly": 10,
        "average_check": 15000,
        "additional_income_monthly": 50000,
        "employees_count": 5,
        "avg_salary": 80000,
        "has_benefit_employees": True,
        "benefit_employees_count": 1,
        "insurance_benefit_rate": 15,
        "rent_monthly": 100000,
        "utilities_monthly": 20000,
        "office_expenses_monthly": 15000,
        "marketing_budget_monthly": 50000,
        "cost_per_client_monthly": 5000,
        "other_fixed_expenses_monthly": 30000,
        "tax_system": "USN_Income_Minus_Expenses",
        "tax_rate_usn_dr": 15,
        "has_vat": False,
        "insurance_rate_standard": 30,
        "patent_cost": 500000,
        "discount_rate": 15
    }
    
    result = process_request(test_data)
    print(json.dumps(result, indent=2, ensure_ascii=False))