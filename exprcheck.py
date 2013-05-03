# exprcheck.py
'''
Project 3 : Program Checking
============================
In this project you need to perform semantic checks on your program.
There are a few different aspects of doing this.

First, you will need to define a symbol table that keeps track of
previously declared identifiers.  The symbol table will be consulted
whenever the compiler needs to lookup information about variable and
constant declarations.

Next, you will need to define objects that represent the different
builtin datatypes and record information about their capabilities.
See the file MpasType.py.

Finally, you'll need to write code that walks the AST and enforces
a set of semantic rules.  Here is a complete list of everything you'll
need to check:

1.  Names and symbols:

    All identifiers must be defined before they are used.  This includes variables,
    constants, and typenames.  For example, this kind of code generates an error:

       a = 3;              // Error. 'a' not defined.
       var a int;

    Note: typenames such as "int", "float", and "string" are built-in names that
    should be defined at the start of the program.

2.  Types of literals

    All literal symbols must be assigned a type of "int", "float", or "string".  
    For example:

       const a = 42;         // Type "int"
       const b = 4.2;        // Type "float"
       const c = "forty";    // Type "string"
       const d = true;

    To do this assignment, check the Python type of the literal value and attach
    a type name as appropriate.

3.  Binary operator type checking

    Binary operators only operate on operands of the same type and produce a
    result of the same type.   Otherwise, you get a type error.  For example:

        var a int = 2;
        var b float = 3.14;

        var c int = a + 3;    // OK
        var d int = a + b;    // Error.  int + float
        var e int = b + 4.5;  // Error.  int = float
        var f bool = true;

4.  Unary operator type checking.

    Unary operators return a result that's the same type as the operand.

5.  Supported operators

    Here are the operators supported by each type:

    int:      binary { +, -, *, /, ==, !=, >, >=, <, <= }, unary { +, - }
    float:    binary { +, -, *, /, ==, !=, >, >=, <, <= }, unary { +, - }
    string:   binary { +, ==, != }, unary { }
    bool:     binary { ==, != }, unary { ! }

    Attempts to use unsupported operators should result in an error. 
    For example:

        var string a = "Hello" + "World";     // OK
        var string b = "Hello" * "World";     // Error (unsupported op *)

6.  Assignment.

    The left and right hand sides of an assignment operation must be
    declared as the same type.

    Values can only be assigned to variable declarations, not
    to constants.

For walking the AST, use the NodeVisitor class defined in exprast.py.
A shell of the code is provided below.
'''

import sys, re, string, types
from errors import error
from mpasast import *
import mpastype
import mpaslex
from pprint import pprint

class SymbolTable(dict):
    '''
    Class representing a symbol table.  It should provide functionality
    for adding and looking up nodes associated with identifiers.
    '''
    def __init__(self, decl=None):
        super().__init__()
        self.decl = decl
    def add(self, name, value):
        self[name] = value
    def lookup(self, name):
        return self.get(name, None)
    def return_type(self):
        if self.decl:
            return self.decl.returntype
        return None

class symtab(object):
    def __init__(self):
        self.stack = []
        self.root = SymbolTable()
        self.stack.append(self.root)
        self.root.update({
            "int": int_type,
            "float": float_type,
            "string": string_type,
            "bool": boolean_type
        })

    def push(self, enclosure):
        self.stack.append(SymbolTable(decl=enclosure))

    def pop(self):
        self.stack.pop()

    def peek(self):
        return self.stack[-1]

    def scope_level(self):
        return len(self.stack)

    def add_local(self, name, value):
        self.peek().add(name, value)

    def add_root(self, name, value):
        self.root.add(name, value)

    def lookup(self, name):
        for scope in reversed(self.stack):
            hit = scope.lookup(name)
            if hit is not None:
                return hit
        return None

    def n_print(self):
        for indent, scope in enumerate(reversed(self.stack)):
            print("Scope for {}".format("ROOT" if scope.decl is None else scope.decl))
            pprint(scope, indent=indent*4, width=20)

class CheckProgramVisitor(NodeVisitor):
    '''
    Program checking class.   This class uses the visitor pattern as described
    in exprast.py.   You need to define methods of the form visit_NodeName()
    for each kind of AST node that you want to process.

    Note: You will need to adjust the names of the AST nodes if you
    picked different names.
    '''
    def __init__(self):
        self.symtab = symtab()
        self.typemap = {
            int: int_type, 
            float: float_type, 
            str: string_type,
            bool: boolean_type
        }

    def check_type_unary(self, node, op, val):
        if hasattr(val, "type"):
            if op not in val.type.unary_ops:
                error(node.lineno, "Unary operator {} not supported".format(op))
            return val.type

    def check_type_binary(self, node, op, left, right):
        if hasattr(left, "type") and hasattr(right, "type"):
            if left.type != right.type:
                error(node.lineno, "Binary operator {} does not have matching LHS/RHS types".format(op))
                return left.type
            errside = None
            if op not in left.type.binary_ops:
                errside = "LHS"
            if op not in right.type.binary_ops:
                errside = "RHS"
            if errside is not None:
                error(node.lineno, "Binary operator {} not supported on {} of expression".format(op, errside))
            # XXX: right now we just propagate the left type, but we should probably handle error conditions
            return left.type

    def check_type_rel(self, node, op, left, right):
        if hasattr(left, "type") and hasattr(right, "type"):
            if left.type != right.type:
                error(node.lineno, "Relational operator {} does not have matching LHS/RHS types".format(op))
                return left.type
            errside = None
            if op not in left.type.rel_ops:
                errside = "LHS"
            if op not in right.type.rel_ops:
                errside = "RHS"
            if errside is not None:
                error(node.lineno, "Relational operator {} not supported on {} of expression".format(op, errside))
            # XXX: right now we just propagate the left type, but we should probably handle error conditions
            return boolean_type

    def inside_function(self):
        return self.symtab.scope_level() > 1

    def visit_Program(self,node):
        node.symtab = self.symtab
        node.symtab = self.symtab.peek()
        # 1. Visit all of the statements
        for statement in node.statements.statements:
            self.visit(statement)
            # 2. Record the associated symbol table
            if isinstance(statement, AssignmentStatement):
                self.symtab.add_local(statement.location.name, statement.expr)

    def visit_Unaryop(self,node):
        self.visit(node.expr)
        # 1. Make sure that the operation is supported by the type
        type = self.check_type_unary(node, node.op, node.expr)
        # 2. Set the result type to the same as the operand
        node.type = type

    def visit_Binop(self,node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # AM note: both are done in check_type_binary
        self.visit(node.left)
        self.visit(node.right)
        type = self.check_type_binary(node, node.op, node.left, node.right)
        # 3. Assign the result type
        node.type = type

    def visit_Relop(self,node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # AM note: both are done in check_type_binary
        self.visit(node.left)
        self.visit(node.right)
        type = self.check_type_rel(node, node.op, node.left, node.right)
        # 3. Assign the result type
        node.type = type

    def visit_AssignmentStatement(self,node):
        if not self.inside_function():
            error(node.lineno, "Cannot assign variable '{}' outside function body".format(node.location.name))
            return
        # 1. Make sure the location of the assignment is defined
        sym = self.symtab.lookup(node.location.name)
        if not sym:
            error(node.lineno, "name '{}' not defined".format(node.location.name))
        # 2. Check that assignment is allowed
        self.visit(node.expr)
        if isinstance(sym, VarDeclaration):
            # empty var declaration, so check against the declared type name
            if hasattr(sym, "type") and hasattr(node.expr, "type"):
                declared_type = sym.type
                value_type = node.expr.type
                if declared_type != value_type:
                    error(node.lineno, "Cannot assign {} to {}".format(value_type, declared_type))
                    return
        if isinstance(sym, ConstDeclaration):
            error(node.lineno, "Cannot assign to constant {}".format(sym.name))
            return
        # 3. Check that the types match
        if hasattr(node.location, "type") and hasattr(node.expr, "type"):
            declared_type = node.location.type
            value_type = node.expr.type
            if declared_type != value_type:
                error(node.lineno, "Cannot assign {} to {}".format(value_type, declared_type))

    def visit_IfStatement(self,node):
        if not self.inside_function():
            error(node.lineno, "Cannot use if statement outside function body")
            return
        self.visit(node.expr)
        if node.expr.type != boolean_type:
            error(node.lineno, "Expression in if statement must evaluate to bool")
        self.visit(node.truebranch)
        if node.falsebranch is not None:
            self.visit(node.falsebranch)

    def visit_WhileStatement(self,node):
        if not self.inside_function():
            error(node.lineno, "Cannot use while statement outside function body")
            return
        self.visit(node.expr)
        if node.expr.type != boolean_type:
            error(node.lineno, "Expression in while statement must evaluate to bool")
        self.visit(node.truebranch)

    def visit_ConstDeclaration(self,node):
        node.scope_level = self.symtab.scope_level()
        # 1. Check that the constant name is not already defined
        if self.symtab.lookup(node.name) is not None:
            error(node.lineno, "Attempted to redefine const '{}', not allowed".format(node.name))
        # 2. Add an entry to the symbol table
        self.symtab.add_local(node.name, node)
        self.visit(node.expr)
        node.type = node.expr.type

    def visit_FuncStatement(self, node):
        # 1. Check that the variable name is not already defined
        node.scope_level = self.symtab.scope_level()
        if node.scope_level > 1:
            error(node.lineno, "Nested functions not implemented")
            return
        self.symtab.push(node)
        if self.symtab.lookup(node.name) is not None:
            error(node.lineno, "Attempted to redefine func '{}', not allowed".format(node.name))
            return
        # 2. Add an entry to the symbol table, and also create a nested symbol
        # table for the function statement
        self.symtab.add_root(node.name, node)
        # 3. Propagate the returntype as a checktype for the function, for 
        # use in function call checking and return statement checking
        if hasattr(node.returntype, "type"):
            node.type = node.returntype.type
        self.visit(node.parameters)
        self.visit(node.expr)
        self.symtab.pop()

    def visit_FuncParameterList(self, node):
        for parameter in node.parameters:
            self.visit(parameter)

    def visit_FuncParameter(self, node):
        self.symtab.add_local(node.name, node)
        node.scope_level = self.symtab.scope_level()
        self.visit(node.typename)
        node.type = node.typename.type

    def visit_FuncCall(self, node):
        if not self.inside_function():
            error(node.lineno, "Cannot call function from outside function body; see main() for entry point")
            return
        sym = self.symtab.lookup(node.name)
        if not sym:
            elf.symtab.n_print()
            error(node.lineno, "Function name '{}' not found".format(node.name))
            return
        if not isinstance(sym, FuncStatement):
            error(node.lineno, "Tried to call non-function '{}'".format(node.name))
            return
        if len(sym.parameters) != len(node.arguments):
            error(node.lineno, "Number of arguments for call to function '{}' do not match function parameter declaration on line {}".format(node.name, sym.lineno))
        self.visit(node.arguments)
        argerrors = False
        for arg, parm in zip(node.arguments.arguments, sym.parameters.parameters):
            if arg.type != parm.type:
                error(node.lineno, "Argument type '{}' does not match parameter type '{}' in function call to '{}'".format(arg.type.typename, parm.type.typename, node.name))
                argerrors = True
            if argerrors:
                return
            arg.parm = parm

    def visit_FuncCallArguments(self, node):
        for argument in node.arguments:
            self.visit(argument)

    def visit_ReturnStatement(self, node):
        self.visit(node.expr)
        if self.symtab.peek().return_type() != node.expr.type:
            error(node.lineno, "Type of return statement expression does not match declared return type for function")
            return

    def visit_PrintStatement(self, node):
        if not self.inside_function():
            error(node.lineno, "Cannot use print statement outside function body")
            return
        self.visit(node.expr)

    def visit_VarDeclaration(self,node):
        # 1. Check that the variable name is not already defined
        if self.symtab.lookup(node.name) is not None:
            error(node.lineno, "Attempted to redefine var '{}', not allowed".format(node.name))
            return
        # 2. Add an entry to the symbol table
        self.symtab.add_local(node.name, node)
        # 3. Check that the type of the expression (if any) is the same
        self.visit(node.typename)
        # propagate type from Typename up to Var declaration
        if hasattr(node.typename, "type"):
            node.type = node.typename.type
        # 4. If there is no expression, set an initial value for the value
        self.visit(node.expr)
        if node.expr is None:
            default = node.type.default
            node.expr = Literal(default)
            node.expr.type = node.type
        node.scope_level = self.symtab.scope_level()

    def visit_Typename(self,node):
        # 1. Make sure the typename is valid and that it's actually a type
        sym = self.symtab.lookup(node.name)
        if not isinstance(sym, MpasType):
            error(node.lineno, "{} is not a valid type".format(node.name))
            return
        node.type = sym

    def visit_Location(self,node):
        # 1. Make sure the location is a valid variable or constant value
        sym = self.symtab.lookup(node.name)
        if not sym:
            error(node.lineno, "name '{}' not found".format(node.name))
        # 2. Assign the type of the location to the node
        node.type = sym.type

    def visit_LoadLocation(self, node):
        # 1. Make sure the loaded location is valid
        sym = self.symtab.lookup(node.location.name)
        if not sym:
            error(node.lineno, "name '{}' not found".format(node.location.name))
            return
        # 2. Assign the appropriate type
        if isinstance(sym, MpasType):
            error(node.lineno, "cannot use {} outside of variable declarations".format(sym.typename))
            return
        type = sym.type
        if type is None:
            error(node.lineno, "Using unrecognized type {}".format(valtype))
        node.type = type

    def visit_Literal(self,node):
        # Attach an appropriate type to the literal
        valtype = type(node.value)
        type = self.typemap.get(valtype, None)
        if type is None:
            error(node.lineno, "Using unrecognized type {}".format(valtype))
        node.type = type
        
# ----------------------------------------------------------------------
#                       DO NOT MODIFY ANYTHING BELOW       
# ----------------------------------------------------------------------

def check_program(node):
    '''
    Check the supplied program (in the form of an AST)
    '''
    checker = CheckProgramVisitor()
    checker.visit(node)

if __name__ == '__main__':

    import mpasparse

    from errors import subscribe_errors
    lexer = mpaslex.make_lexer()
    parser = mpasparse.make_parser()
    with subscribe_errors(lambda msg: sys.stdout.write(msg+"\n")):
        program = parser.parse(open(sys.argv[1]).read())
        # Check the program
        check_program(program)
        #program.symtab.print()