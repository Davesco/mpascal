#  ---------------------------------------------------------------
#  GENERACION TABLA DE SIMBOLOS
#  ---------------------------------------------------------------

class Symtab:
	'''
	Una tabla de símbolos.  Este es un objecto simple que mantiene
	una tabla hash de nombres de simbolos y los nodos de 
	Declaration o FunctionDefn a los que refiere.
	
	Hay una tabla de símbolos para cada elemento de código que 
	tiene su propio ámbito (por ejemplo, cada declaración compuesta
	tendrá su propia tabla de símbolos).  Como resultado de ello,
	las tablas de símbolos pueden ser anidadas si los elementos del
	código son anidados y las búsquedas en ella serán recursivas
	hacia arriba a traves de los padres para representar las reglas
	de ámbito léxico.
	'''
	class SymbolDefinedError(Exception):
		'''
		Excepción generada cuando el código intenta de agregar un
		símbol a la tabla en la que el símbol ya está definido.
		Tenga en cuenta que 'definido' es usado en el sentido de
		mpascal --pe., 'espacio que se ha localizado para el símbol',
		lo cual es opuesto a delcaración.
		'''

		pass

	class SymbolConflictError(Exception):
		'''
		Excepción generada cuando el código trata de agregar un
		símbol a la tabla en la que el símbol ya está definido y
		su tipo difiere del símbol previamente definido.
		'''

		pass

	def __init__(self, parent=None):
		'''
		Crea una tabla se símbol vacia con la tabla de símbol
		padre.
		'''

		self.entries = {}
		self.parent = parent
		if self.parent != None:
			self.parent.children.append(self)
		self.children = []
	
	def add(self, name, value):
		'''
		Agrega un símbol con el valor dado a la tabla de símbol.
		El valor es usualmente un nodo del AST que representa la
		declaración o definición de una función/variable (p.e.,
		Declaration o FunctionDefn).
		'''
		
		if self.entries.has_key(name):
			if not self.entries[name].extern:
				raise Symtab.SymbolDefinedError()
			elif self.entries[name].type.get_string() != \
				value.type.get_string():
				raise Symtab.SymbolConflictError()
		self.entries[name] = value

	def get(self, name):
		'''
		Recupera el símbol con el nombre dado desde la tabla de
		símbolos, recursivamente hacia arriba a través del padre
		si no se encuentra en la actual.
		'''

		if self.entries.has_key(name):
			return self.entries[name]
		else:
			if self.parent != None:
				return self.parent.get(name)
			else:
				return None


#  ---------------------------------------------------------------
#  Agragar los siguientes dos métodos en CheckProgramVisitor.
#  ---------------------------------------------------------------

def push_symtab(self, node):
	'''
	Inserta una tabla de símbolos dentro de la pila de tablas de
	símbolos del visitor y adjunta esta tabla de símbolos al nodo
	dado.  Se utiliza siempre que un ámbito léxico es encontrado,
	por lo que el nodo es un objeto CompoundStatement.
	'''

	self.curr_symtab = Symtab(self.curr_symtab)
	node.symtab = self.curr_symtab

def pop_symtab(self):
	'''
	Extrae una tabla de símbolos de la pila de tablas de símbol
	del visitor.  Se utiliza cuando se sale de un ámbito léxico.
	'''

	self.curr_symtab = self.curr_symtab.parent
