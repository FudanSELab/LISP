package edu.lisp.visitor;

import org.eclipse.jdt.core.dom.ASTVisitor;
import org.eclipse.jdt.core.dom.CompilationUnit;
import org.eclipse.jdt.core.dom.EnumDeclaration;
import org.eclipse.jdt.core.dom.TypeDeclaration;

import java.util.ArrayList;
import java.util.List;

public class DeclarationVisitor extends ASTVisitor {
    public CompilationUnit cu;
    public List<TypeDeclaration> types = new ArrayList<>();
    public List<EnumDeclaration> enums = new ArrayList<>();

    @Override
    public boolean visit(CompilationUnit node) {
        cu = node;
        return super.visit(node);
    }

    @Override
    public boolean visit(TypeDeclaration node) {
        if (node.isMemberTypeDeclaration() || node.isPackageMemberTypeDeclaration())
            types.add(node);
        return super.visit(node);
    }

    @Override
    public boolean visit(EnumDeclaration node) {
        if (node.isMemberTypeDeclaration() || node.isPackageMemberTypeDeclaration())
            enums.add(node);
        return super.visit(node);
    }
}
