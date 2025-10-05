with open('services/cvss_calculator.py', 'r') as f:
    lines = f.readlines()

# Find and replace the _round_up method
new_lines = []
in_round_up = False
skip_count = 0

for i, line in enumerate(lines):
    if 'def _round_up(self, score: float) -> float:' in line:
        # Replace the entire method
        new_lines.append('    def _round_up(self, score: float) -> float:\n')
        new_lines.append('        """Round up to 1 decimal place, capped at 10.0"""\n')
        new_lines.append('        if score <= 0:\n')
        new_lines.append('            return 0.0\n')
        new_lines.append('        rounded = round(score + 0.05, 1)\n')
        new_lines.append('        return min(rounded, 10.0)\n')
        in_round_up = True
        skip_count = 2  # Skip next 2 lines (docstring and return)
    elif skip_count > 0:
        skip_count -= 1
        continue
    else:
        in_round_up = False
        new_lines.append(line)

with open('services/cvss_calculator.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Fixed CVSS _round_up method")
