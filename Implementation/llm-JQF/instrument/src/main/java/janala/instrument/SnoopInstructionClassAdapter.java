
package janala.instrument;

import org.objectweb.asm.ClassVisitor;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;


public class SnoopInstructionClassAdapter extends ClassVisitor {
  private final String className;
  private String superName;

  public SnoopInstructionClassAdapter(ClassVisitor cv, String className) {
    super(Opcodes.ASM8, cv);
    this.className = className;
  }

  @Override
  public void visit(int version,
                    int access,
                    String name,
                    String signature,
                    String superName,
                    String[] interfaces) {
//    System.out.println("n cn: " + name + "," + this.className);
    assert name.equals(this.className);
    this.superName = superName;

    String[] newInterfaces = interfaces;
    if (this.className.startsWith("com/pholser/junit/")) {
      // Here I must jump com/pholser/junit, Otherwise, it would report:
      // "Attempt to create proxy for a non-annotation type."
      // And I don't know why and what happened.
    } else {
//      System.out.println("so I instrument this class: " + this.className);
      newInterfaces = checkAndInsertSerializable(interfaces);
    }

    cv.visit(version, access, name, signature, superName, newInterfaces);
  }

  private String[] checkAndInsertSerializable(String[] interfaces) {
    // if existed, return interfaces directly
    for (String i : interfaces) {
      if (i.equals("java/io/Serializable")) {
        return interfaces;
      }
    }

    // else, add java/io/Serializable
    String[] newInterfaces = new String[interfaces.length + 1];
    System.arraycopy(interfaces, 0, newInterfaces, 0, interfaces.length);
    newInterfaces[interfaces.length] = "java/io/Serializable";
    return newInterfaces;
  }

  @Override
  public MethodVisitor visitMethod(int access, String name, String desc,
      String signature, String[] exceptions) {
    MethodVisitor mv = cv.visitMethod(access, name, desc, signature, exceptions);
    if (mv != null) {
      if(Config.instance.useFastCoverageInstrumentation){
        return new FastCoverageMethodAdapter(mv, className, name, desc, superName, GlobalStateForInstrumentation.instance);
      }else {
        return new SnoopInstructionMethodAdapter(mv, className, name, desc, superName,
                GlobalStateForInstrumentation.instance, (access & Opcodes.ACC_STATIC) != 0);
      }
    }
    return null;
  }
}
