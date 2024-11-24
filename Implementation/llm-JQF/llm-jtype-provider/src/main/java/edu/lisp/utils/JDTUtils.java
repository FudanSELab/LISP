package edu.lisp.utils;

import edu.lisp.visitor.DeclarationVisitor;
import org.eclipse.jdt.core.JavaCore;
import org.eclipse.jdt.core.dom.AST;
import org.eclipse.jdt.core.dom.ASTParser;
import org.eclipse.jdt.core.dom.CompilationUnit;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Hashtable;

public class JDTUtils {
    public static CompilationUnit getCompilationUnit(String filePath) {
        return getCompilationUnit(new File(filePath));
    }

    public static CompilationUnit getCompilationUnit(File file) {
        CompilationUnit cu = null;
        try {
            String source = new String(Files.readAllBytes(file.toPath()));
            cu = getCompilationUnit(source.toCharArray());
        } catch (IOException e) {
            e.printStackTrace();
        }
        return cu;
    }

    private static CompilationUnit getCompilationUnit(char[] source) {
        ASTParser astParser = ASTParser.newParser(AST.JLS11);
        astParser.setKind(ASTParser.K_COMPILATION_UNIT);

        Hashtable<String, String> options = JavaCore.getOptions();
        options.put(JavaCore.COMPILER_COMPLIANCE, JavaCore.VERSION_1_8);
        options.put(JavaCore.COMPILER_CODEGEN_TARGET_PLATFORM, JavaCore.VERSION_1_8);
        options.put(JavaCore.COMPILER_SOURCE, JavaCore.VERSION_1_8);
        options.put(JavaCore.COMPILER_DOC_COMMENT_SUPPORT, JavaCore.ENABLED);
        astParser.setCompilerOptions(options);

        astParser.setResolveBindings(true);
        astParser.setBindingsRecovery(true);

        astParser.setSource(source);
        return (CompilationUnit) astParser.createAST(null);
    }

    public static boolean isCuHasPackageDecl(CompilationUnit cu) {
        if (cu.getPackage() != null)
            return true;
        else{
            return false;
        }
    }

    public static DeclarationVisitor visitCu(CompilationUnit cu) {
        DeclarationVisitor visitor = new DeclarationVisitor();
        cu.accept(visitor);
        return visitor;
    }

    public static boolean isCuHasTypeDecl(DeclarationVisitor visitor) {
        return !visitor.types.isEmpty();
    }
}
