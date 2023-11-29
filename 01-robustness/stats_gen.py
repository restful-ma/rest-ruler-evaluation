import matplotlib.pyplot as plt
import pandas as pd

# bar chart for violation distribution
df = pd.read_csv('stats/rule_output.csv', sep=';')

plt.figure()
df.transpose()
fig = df.sort_values(by='appearances').plot.barh(x="rule")

fig.bar_label(fig.containers[0])
fig.legend(loc='lower right')
plt.savefig('stats/violations.png', bbox_inches='tight')

# severity
df1 = pd.read_csv('stats/severity_output.csv', sep=';')
print(df1)
plt.figure()

fig1 = df1.sort_values(by='appearances').plot.bar(x="severity")
fig1.bar_label(fig1.containers[0])
plt.savefig('stats/severity.png', bbox_inches='tight')

# quality attrib

df2 = pd.read_csv('stats/attributes_output.csv', sep=';')
print(df2)
plt.figure()
fig2 = df2.sort_values(by='appearances').plot.bar(x="attributes")
fig2.bar_label(fig2.containers[0])
plt.savefig('stats/attributes.png', bbox_inches='tight')