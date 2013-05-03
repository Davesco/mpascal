#  ---------------------------------------------------------------
#  GENERACION TABLA DE SIMBOLOS
#  ---------------------------------------------------------------

class Symtab:
	'''
	Una tabla de s�mbolos.  Este es un objecto simple que mantiene
	una tabla hash de nombres de simbolos y los nodos de 
	Declaration o FunctionDefn a los que refiere.
	
	Hay una tabla de s�mbolos para cada elemento de c�digo que 
	tiene su propio �mbito (por ejemplo, cada declaraci�n compuesta
	tendr� su propia tabla de s�mbolos).  Como resultado de ello,
	las tablas de s�mbolos pueden ser anidadas si los elementos del
	c�digo son anidados y las b�squedas en ella ser�n recursivas
	hacia arriba a traves de los padres para representar las reglas
	de �mbito l�xico.
	'''
	class SymbolDefinedError(Exception):
		'''
		Excepci�n generada cuando el c�digo intenta de agregar un
		s�mbol a la tabla en la que el s�mbol ya est� definido.
		Tenga en cuenta que 'definido' es usado en el sentido de
		mpascal --pe., 'espacio que se ha localizado para el s�mbol',
		lo cual es opuesto a delcaraci�n.
		'''

		pass

	class SymbolConflictError(Exception):
		'''
		Excepci�n generada cuando el c�digo trata de agregar un
		s�mbol a la tabla en la que el s�mbol ya est� definido y
		su tipo difiere del s�mbol previamente definido.
		'''

		pass

	def __init__(self, parent=None):
		'''
		Crea una tabla se s�mbol vacia con la tabla de s�mbol
		padre.
		'''

		self.entries = {}
		self.parent = parent
		if self.parent != None:
			self.parent.children.append(self)
		self.children = []
	
	def add(self, name, value):
		'''
		Agrega un s�mbol con el valor dado a la tabla de s�mbol.
		El valor es usualmente un nodo del AST que representa la
		declaraci�n o definici�n de una funci�n/variable (p.e.,
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
		Recupera el s�mbol con el nombre dado desde la tabla de
		s�mbolos, recursivamente hacia arriba a trav�s del padre
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
#  Agragar los siguientes dos m�todos en CheckProgramVisitor.
#  ---------------------------------------------------------------

def push_symtab(self, node):
	'''
	Inserta una tabla de s�mbolos dentro de la pila de tablas de
	s�mbolos del visitor y adjunta esta tabla de s�mbolos al nodo
	dado.  Se utiliza siempre que un �mbito l�xico es encontrado,
	por lo que el nodo es un objeto CompoundStatement.
	'''

	self.curr_symtab = Symtab(self.curr_symtab)
	node.symtab = self.curr_symtab

def pop_symtab(self):
	'''
	Extrae una tabla de s�mbolos de la pila de tablas de s�mbol
	del visitor.  Se utiliza cuando se sale de un �mbito l�xico.
	'''

	self.curr_symtab = self.curr_symtab.parent
