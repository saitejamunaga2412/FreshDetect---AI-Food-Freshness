import os

def cnt(p):
  c=0
  for root, dirs, files in os.walk(p):
    c += sum(1 for f in files if f.lower().endswith(('.jpg', '.png', '.jpeg')))
  return c

for d in os.listdir('datasets_optional/Fruit16K'):
  print(f"{d}: {cnt(os.path.join('datasets_optional/Fruit16K', d))}")
