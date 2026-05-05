import re
import dns.resolver
import smtplib

def check_syntax(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def get_mx_records(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return [str(r.exchange) for r in records]
    except:
        return []

def check_spf(domain):
    try:
        records = dns.resolver.resolve(domain, 'TXT')
        for r in records:
            if "v=spf1" in str(r):
                return True
    except:
        pass
    return False

def smtp_check(mx, email):
    try:
        server = smtplib.SMTP(timeout=10)
        server.connect(mx)
        server.helo("test.com")
        server.mail("test@test.com")
        code, _ = server.rcpt(email)
        server.quit()
        return code
    except:
        return None

def catch_all_test(mx, domain):
    fake_email = f"random123456@{domain}"
    return smtp_check(mx, fake_email)

def verify_email(email):
    result = {}

    # Step 1: Syntax
    result['syntax'] = check_syntax(email)
    if not result['syntax']:
        return result

    domain = email.split("@")[1]

    # Step 2: MX
    mx_records = get_mx_records(domain)
    result['mx_found'] = len(mx_records) > 0

    if not result['mx_found']:
        return result

    mx = mx_records[0]

    # Step 3: SPF
    result['spf'] = check_spf(domain)

    # Step 4: SMTP
    smtp_code = smtp_check(mx, email)
    result['smtp_code'] = smtp_code

    # Step 5: Catch-all
    fake_code = catch_all_test(mx, domain)
    result['catch_all'] = fake_code == 250

    return result


# # TEST
# email = "shraddha@palmonas.com"
# print(verify_email(email))