from markdown.preprocessors import Preprocessor
from markdown.blockprocessors import BlockProcessor
from markdown.postprocessors import Postprocessor
from markdown.util import etree
from markdown.util import AtomicString
from markdown.extensions import Extension
import re

class TabbedNavPre(Preprocessor):
	"""
	*Bootstrap Tabbed Navigation preprocessor*.
	
	Necessary if the tabbed content was originally converted from
	wikitext from https://buddycloud.org/wiki,
	therefore formatted like this:

	<tabbed>
	KEY=
	VALUE
	|-| KEY2=
	VALUE
	...
	|-| KEYn=
	VALUE
	</tabbed>

	This preprocessor will transform that into this:

	{@
	{@[KEY]}
	{@[KEY2]}
	...
	{@[KEYn]}
	@}
	{{@
	{{@[KEY]
	VALUE
	/@}}
	{{@[KEY2]
	VALUE
	/@}}
	...
	{@[KEYn]
	VALUE
	/@}}
	@}}

	Which will be easier to be handled by our postprocessor.
	"""

	def __init__(self):

		self.brkstartre = re.compile("^.*< *tabber *>")
		self.brkendre = re.compile("^.*< */tabber *>")

	def run(self, lines):

		new_lines = []
		tabbed_block = ""
		inside_block = False

		while ( len(lines) != 0 ):
			
			line = lines[0]

		#Is it just starting a new tabbed block?
			if line.strip().startswith("<tabber>"):
				inside_block = True

		#Does it have </tabber> ending tags in the middle of the line?
			if ( not line.strip().startswith("</tabber>")
			     and self.brkendre.match(line.strip()) ):
				split = [line[:line.find("</tabber>")],
					line[line.find("</tabber>"):] ]
				lines.pop(0)
				lines.insert(0, split[1])
				lines.insert(0, split[0])
				continue

		#What about <tabber> starting tags?
			if ( not line.strip().startswith("<tabber>")
			     and self.brkstartre.match(line.strip()) ):
				split = [line[:line.find("<tabber>")],
					line[line.find("<tabber>"):] ]
				lines.pop(0)
				lines.insert(0, split[1])
				lines.insert(0, split[0])
				continue

		#Is the line empty, within a tabbed block?
			if line.strip() == "" and inside_block:
				line = "\n"

		#If inside block, store line content
		#to be added as a single line later
			if inside_block:
				tabbed_block += "\n" + line
		#Otherwise just add new line
			else:
				new_lines.append(line)
			lines.pop(0)

		#Is it finishing a tabbed block?
			if line.startswith("</tabber>"):
				inside_block = False
				new_lines.append(tabbed_block)
				tabbed_block = ""

		i = 0
		while ( i < len(new_lines) ):

			line = new_lines[i]
			i += 1

		#Is this line representing a tabbed content?
			if line.strip().startswith("<tabber>"):

				i -= 1
			#Swap this line for a bunch of other lines
			#with a different structure representing
			#the tabbed content
				new_lines = new_lines[:i] + new_lines[i+1:]

				keys = []
				values = {}

				line = line.replace("<tabber>", "")
				line = line.replace("</tabber>", "")

				for keyval in line.split("|-|"):
					sep = keyval.find("=")
					key = keyval[:sep].strip()
					val = keyval[sep+1:]
					keys.append(key)
					values[key] = val

				new_lines.insert(i, "{@")
				i += 1
				for key in keys:
					new_lines.insert(i, "{@[%s]}" % key)
					i += 1
				new_lines.insert(i, "@}")
				i += 1

				new_lines.insert(i, "{{@")
				i += 1
				for key in keys:
					new_lines.insert(i, "{{@[%s]" % key)
					i += 1
					content_lines = values[key].split("\n")
					for c_line in content_lines:
						new_lines.insert(i, c_line)
						i += 1
					new_lines.insert(i, "/@}}")
					i += 1
				new_lines.insert(i, "@}}")
				i += 1

		#Now make sure there's at least one blank line amidst each
		#Tabbed Nav block (Bootstrap Tooglable Navs Markdown syntax)

		add_blanks_at = []
		aftertabcontentdefre = re.compile("{{@\[.*\]$")

		for i in range(len(new_lines)):

			line = new_lines[i]

			if line == "{@":
				add_blanks_at.append(i)
			elif line == "/@}}":
				add_blanks_at.append(i)
			elif line == "@}}":
				add_blanks_at.append(i+1)
			elif aftertabcontentdefre.match(line):
				add_blanks_at.append(i+1)

		for k in range(len(add_blanks_at)):
			print "inserting at: ", add_blanks_at[k]
			new_lines.insert(add_blanks_at[k], "\n")
			for j in range(k+1, len(add_blanks_at)):
				add_blanks_at[j] += 1

		for k in new_lines:
			print k
		return new_lines

class TabbedNavBlockProcessor(BlockProcessor):

	def __init__(self):
		pass

	def test(self, parent, block):

		print "PARENT: "
		print parent.text
		print "IS THIS BLOCK: "
		print block
		print "A TABBED NAV BLOCK?"

		veredict = ( ( block.startswith("{@\n{@[")
				and block.endswith("]") )
			or   ( block.startswith("/@}}\n{{@[")
				and block.endswith("]") )
			or   ( block.startswith("/@}}\n@}}") ) )

		print "VEREDICT:", veredict
		return veredict

	def run(self, parent, blocks):

		tabbed_nav = etree.SubElement(parent, "tabbed_nav")
		tabbed_nav.text = AtomicString(blocks[0])
		blocks.pop(0)

class TabbedNavPost(Postprocessor):
	"""
	*Bootstrap Tabbed Navigation postprocessor*.

	Processes our newly defined Markdown syntax
	for creating Bootstrap Togglable tabs.

	Since Bootstrap requires two HTML elements to compose Tooglable tabs,
	we also decided it would be easier to implement the transformation if
	the Markdown syntax also contained two sections, as follows:

	There's the *Tab Key declaration* section and the *Tab Content declaration* section.

	Tab Key declaration sections must be surrounded by the following lines:

	{@
	@}

	And each line amidst those will contain a Tab Key declaration and should be as follows:

	{@[ KEY ]} where KEY can be any character

	Tab Content declaration sections must be surrounded by the following lines:

	{{@
	@}}

	And each block of lines amidst those will contain a Tab Content declaration. Remember, it is a block of lines. That block of lines must be surrounded by the following lines:

	{{@[ KEY ] where KEY must match a key declared at Tab Key declarations
	/@}}

	The lines amidst those will be the content of your tabs.
	Feel free to use anything defined by the Default Markdown syntax.

	Example Usage:

	{@
	{@[KEY]}
	{@[KEY2]}
	...		(denoting multiple declarations in between)
	{@[KEYn]}
	@}
	{{@
	{{@[KEY]
	...
	Your Markdown content for this tab
	...
	/@}}
	{{@[KEY2]
	...
	Your Markdown content for this tab
	/@}}
	...		(denoting multiple declarations in between
	{@[KEYn]
	...
	Your Markdown content for this tab
	...
	/@}}
	@}}
 
	"""

	def __init__(self):

		self.starttabsre = re.compile("(?<!{){@\s+")
		self.tabkeydeclre = re.compile("(?<!{){@\[.*\]}")
		self.endtabsre = re.compile("@}\s+")
		self.startcontentsre = re.compile("{{@\s+")
		self.tabcontentdeclre = re.compile("{{@\[.*\]\s*")
		self.endcontentsre = re.compile("/?@}}")

	def tabkeydeclrepl(self, matchobj):
		
		matched = matchobj.group(0).strip()
		key = matched.replace("{@[", "").replace("]}", "")
		html = "\t<li><a href='#id_%s' data-toggle='tab'>%s</a></li>"
		return html % (key.replace(" ", "_").lower(), key)

	def tabcontentdeclrepl(self, matchobj):

		matched = matchobj.group(0).strip()
		key = matched.replace("{{@[", "").replace("]", "")
		html = "\t<div class='tab-pane' id='id_%s'>\n\t\t"
		return html % key.replace(" ", "_").lower()

	def endingcontentsrepl(self, matchobj):

		matched = matchobj.group(0).strip()
		html = "</div>"
		return "\t" + html if matched.startswith("/") else html	

	def run(self, text):

	#Removing the surrounding <tabbed_nav> and </tabbed_nav`> tags
		text = text.replace("<tabbed_nav>", "")
		text = text.replace("</tabbed_nav>", "")

	#Replacing all proper starting flags by bootstrap nav tab <ul> tags
		html = "<ul class='nav nav-tabs'>\n"
		text = re.sub(self.starttabsre, html, text)

	#Replacing all proper starting flags by bootstrap tab content <div> tags
		html = "<div class='tab-content'>\n"
		text = re.sub(self.startcontentsre, html, text)

	#Replacing all nav tab declarations by bootstrap <li><a> tags
		text = re.sub(self.tabkeydeclre, self.tabkeydeclrepl, text)

	#Replacing all tab pane declarations by bootstrap <div> tags
		text = re.sub(self.tabcontentdeclre, 
			self.tabcontentdeclrepl, text)

	#Replacing all proper ending flags by bootstrap </ul> tags
		html = "</ul>\n"
		text = re.sub(self.endtabsre, html, text)

	#Replacing all proper ending flags by bootstrap </div> tags
		text = re.sub(self.endcontentsre, 
			self.endingcontentsrepl, text)

		return text

class Bootstrap_Markdown_Extension(Extension):

	def extendMarkdown(self, md, md_globals):
		md.preprocessors.add('tabbed_nav', TabbedNavPre(), "_begin")
		md.postprocessors.add('tabbed_nav', TabbedNavPost(), "_begin")
		md.parser.blockprocessors.add('tabbed_nav',
			TabbedNavBlockProcessor(), "_begin")

def makeExtension(configs=None):
	return Bootstrap_Markdown_Extension(configs=configs)