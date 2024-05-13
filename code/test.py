from Levenshtein import ratio
t = ["hello", "bello", "grime"]
x =[]
for i in range(0, len(t)):
     for j in range(0, len(t)):
             if i == j:
                     continue
             elif ratio(t[i], t[j]) < 0.8:
                     x.append(t[i])
                     continue


print(x)
