from app import app

print("All registered routes:")
print("=" * 60)
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint:30s} {rule.rule}")
print("=" * 60)
print("\nAdmin routes only:")
print("=" * 60)
for rule in app.url_map.iter_rules():
    if 'admin' in rule.rule or 'admin' in rule.endpoint:
        print(f"{rule.endpoint:30s} {rule.rule}")
