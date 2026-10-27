# Generated from dsl/FrameworkSpec.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .FrameworkSpecParser import FrameworkSpecParser
else:
    from FrameworkSpecParser import FrameworkSpecParser

# This class defines a complete listener for a parse tree produced by FrameworkSpecParser.
class FrameworkSpecListener(ParseTreeListener):

    # Enter a parse tree produced by FrameworkSpecParser#start.
    def enterStart(self, ctx:FrameworkSpecParser.StartContext):
        pass

    # Exit a parse tree produced by FrameworkSpecParser#start.
    def exitStart(self, ctx:FrameworkSpecParser.StartContext):
        pass


    # Enter a parse tree produced by FrameworkSpecParser#decl.
    def enterDecl(self, ctx:FrameworkSpecParser.DeclContext):
        pass

    # Exit a parse tree produced by FrameworkSpecParser#decl.
    def exitDecl(self, ctx:FrameworkSpecParser.DeclContext):
        pass


    # Enter a parse tree produced by FrameworkSpecParser#entry.
    def enterEntry(self, ctx:FrameworkSpecParser.EntryContext):
        pass

    # Exit a parse tree produced by FrameworkSpecParser#entry.
    def exitEntry(self, ctx:FrameworkSpecParser.EntryContext):
        pass


    # Enter a parse tree produced by FrameworkSpecParser#member.
    def enterMember(self, ctx:FrameworkSpecParser.MemberContext):
        pass

    # Exit a parse tree produced by FrameworkSpecParser#member.
    def exitMember(self, ctx:FrameworkSpecParser.MemberContext):
        pass


    # Enter a parse tree produced by FrameworkSpecParser#argType.
    def enterArgType(self, ctx:FrameworkSpecParser.ArgTypeContext):
        pass

    # Exit a parse tree produced by FrameworkSpecParser#argType.
    def exitArgType(self, ctx:FrameworkSpecParser.ArgTypeContext):
        pass


    # Enter a parse tree produced by FrameworkSpecParser#variant.
    def enterVariant(self, ctx:FrameworkSpecParser.VariantContext):
        pass

    # Exit a parse tree produced by FrameworkSpecParser#variant.
    def exitVariant(self, ctx:FrameworkSpecParser.VariantContext):
        pass


    # Enter a parse tree produced by FrameworkSpecParser#langLine.
    def enterLangLine(self, ctx:FrameworkSpecParser.LangLineContext):
        pass

    # Exit a parse tree produced by FrameworkSpecParser#langLine.
    def exitLangLine(self, ctx:FrameworkSpecParser.LangLineContext):
        pass


    # Enter a parse tree produced by FrameworkSpecParser#wrapLine.
    def enterWrapLine(self, ctx:FrameworkSpecParser.WrapLineContext):
        pass

    # Exit a parse tree produced by FrameworkSpecParser#wrapLine.
    def exitWrapLine(self, ctx:FrameworkSpecParser.WrapLineContext):
        pass



del FrameworkSpecParser