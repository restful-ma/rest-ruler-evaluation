import matplotlib.pyplot as plt
import pandas as pd

# bar chart for violation distribution
df = pd.read_csv('statsv2/rule_output.csv', sep=';')
print("Total violations:", df["appearances"].sum())
plt.figure(frameon=False)
df.transpose()
# remove not included rule
# df = df.drop(index=6)
# replace with shortened rule identifiers based on actual data
df.iloc[0, 0] = 'MetaInformation'
df.iloc[1, 0] = 'RC401'
df.iloc[2, 0] = 'CamelCase'
df.iloc[3, 0] = 'NoFileExtensions'
df.iloc[4, 0] = 'ForwardSlash'
df.iloc[5, 0] = 'NoUnderscores'
df.iloc[6, 0] = 'SingularNoun'
df.iloc[7, 0] = 'ContentType'
df.iloc[8, 0] = 'GETRetrieve'
df.iloc[9, 0] = 'PluralNoun'
df.iloc[10, 0] = 'NoTunnel'
df.iloc[11, 0] = 'NoCRUDNames'
df.iloc[12, 0] = 'OfficialCodes'
df.iloc[13, 0] = 'VerbController'
df.iloc[14, 0] = 'NoTrailingSlash'
df.iloc[15, 0] = 'NormalizedPaths'

ax = df.sort_values(by='appearances').plot.barh(
    x='rule', legend=None, figsize=(5, 5))
ax.get_yaxis().get_label().set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.bar_label(ax.containers[0])
plt.savefig('statsv2/violations.pdf', dpi=150,
            bbox_inches='tight', transparent=True)

# severity
df = pd.read_csv('statsv2/severity_output.csv', sep=';')
print(df)
plt.figure()

fig1 = df.sort_values(by='appearances').plot.bar(x='severity')
fig1.bar_label(fig1.containers[0])
plt.savefig('statsv2/severity.png', bbox_inches='tight')

# quality attrib

df = pd.read_csv('statsv2/attributes_output.csv', sep=';')
print(df)
plt.figure()
fig2 = df.sort_values(by='appearances').plot.bar(x='attributes')
fig2.bar_label(fig2.containers[0])
plt.savefig('statsv2/attributes.png', bbox_inches='tight')

# descriptive statistics for violation
df = pd.read_csv('statsv2/violation_output.csv', sep=';')
print(df.describe())
