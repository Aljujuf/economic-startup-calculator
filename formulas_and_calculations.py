"""
Модуль формул и базовых расчётов
"""

from typing import List, Optional


def get_business_coefficient(business_type: str) -> float:
    coefficients = {
        "services": 0.85,
        "software": 0.90,
        "saas": 0.70,
        "online_store": 1.20
    }
    return coefficients.get(business_type, 1.0)


def get_revenue_coefficient(income_source: str) -> float:
    coefficients = {
        "services": 1.0,
        "subscription": 1.0,
        "software_sales": 0.9
    }
    return coefficients.get(income_source, 1.0)


def calculate_tax(
    tax_mode: str,
    profit_before_tax: float,
    revenue: float,
    tax_system: str = "USN_Income_Minus_Expenses",
    tax_rate_usn_dr: float = 15,
    has_vat: bool = False,
    patent_cost: float = 0
) -> float:
    profit_before_tax = max(0, profit_before_tax)
    
    if tax_mode == "USN":
        if tax_system == "Income":
            return revenue * 0.06
        else:
            return profit_before_tax * (tax_rate_usn_dr / 100)
    
    elif tax_mode == "OSNO":
        tax = profit_before_tax * 0.20
        if has_vat:
            tax += revenue * 0.20
        return tax
    
    elif tax_mode == "PATENT":
        return patent_cost / 12
    
    return 0


def calculate_monthly_costs(data) -> float:
    """Расчёт постоянных расходов в месяц"""
    payroll = data.employees_count * data.avg_salary
    
    if data.has_benefit_employees and data.benefit_employees_count > 0:
        normal = data.employees_count - data.benefit_employees_count
        insurance = (normal * data.avg_salary * data.insurance_rate_standard / 100) + \
                    (data.benefit_employees_count * data.avg_salary * data.insurance_benefit_rate / 100)
    else:
        insurance = payroll * data.insurance_rate_standard / 100
    
    personnel = payroll + insurance
    
    fixed = (data.rent_monthly + data.utilities_monthly + data.office_expenses_monthly +
             data.marketing_budget_monthly + data.other_fixed_expenses_monthly)
    
    return personnel + fixed


def calculate_monthly_clients(start: int, growth: float, month: int) -> float:
    return start * ((1 + growth / 100) ** month)


def generate_cashflow_series(data, modifiers: Optional[dict] = None) -> List[float]:
    """Генерация помесячных денежных потоков"""
    
    clients_start = data.monthly_customers_start
    growth = data.customers_growth_monthly
    cost_per_client = data.cost_per_client_monthly
    
    if modifiers:
        if 'monthly_customers_start' in modifiers:
            clients_start *= modifiers['monthly_customers_start']
        if 'customers_growth_monthly' in modifiers:
            growth += modifiers['customers_growth_monthly']
        if 'cost_per_client_monthly' in modifiers:
            cost_per_client *= modifiers['cost_per_client_monthly']
    
    fixed_costs = calculate_monthly_costs(data)
    K_biz = get_business_coefficient(data.business_type)
    K_rev = get_revenue_coefficient(data.income_source)
    
    cashflows = [-data.startup_capital]
    total_months = data.planning_years * 12
    
    for month in range(1, total_months + 1):
        clients = calculate_monthly_clients(clients_start, growth, month)
        
        revenue = (clients * data.average_check + data.additional_income_monthly) * K_rev
        var_costs = clients * cost_per_client * K_biz
        
        profit = revenue - var_costs - fixed_costs
        
        tax = calculate_tax(
            tax_mode=data.tax_mode,
            profit_before_tax=profit,
            revenue=revenue,
            tax_system=data.tax_system,
            tax_rate_usn_dr=data.tax_rate_usn_dr,
            has_vat=data.has_vat,
            patent_cost=data.patent_cost
        )
        
        cashflows.append(round(profit - tax, 2))
    
    return cashflows


def aggregate_yearly_cashflow(monthly: List[float], months_per_year: int = 12) -> List[float]:
    yearly = [monthly[0]]
    for year in range(1, len(monthly) // months_per_year + 1):
        start = (year - 1) * months_per_year + 1
        end = start + months_per_year
        yearly.append(round(sum(monthly[start:end]), 2))
    return yearly


def calculate_npv(cashflows: List[float], rate: float) -> float:
    r = rate / 100
    return round(sum(cf / ((1 + r) ** t) for t, cf in enumerate(cashflows)), 2)


def calculate_pi(cashflows: List[float], npv: float) -> float:
    inv = abs(cashflows[0])
    return round((npv + inv) / inv, 3) if inv != 0 else float('inf')


def calculate_payback_period(cashflows: List[float]) -> float:
    cum = 0.0
    prev = 0.0
    for t, cf in enumerate(cashflows):
        cum += cf
        if cum >= 0 and t > 0:
            if abs(cf) < 1e-9:
                return float(t)
            return round((t - 1) + abs(prev) / cf, 2)
        prev = cum
    return float('inf')