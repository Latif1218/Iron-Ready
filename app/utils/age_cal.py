from datetime import date

def calculate_age(birth_date: date) -> int | None:
    if not birth_date:
        return None
    
    today = date.today()
    age = today.year - birth_date.year

    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return max(age, 0) 