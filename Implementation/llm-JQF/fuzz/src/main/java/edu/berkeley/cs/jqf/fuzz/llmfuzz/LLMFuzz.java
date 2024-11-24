package edu.berkeley.cs.jqf.fuzz.llmfuzz;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * The {@link LLMFuzz} annotation marks a method as an entry-point for
 * llm-based fuzz testing
 */
@Target({ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
public @interface LLMFuzz {
    /**
     * The signature of the target method that would be tested.
     *
     * <p>This element is required.</p>
     *
     * <p>e.g. org.example.demo.Class::method(A, B, C)</p>
     *
     * @return signature of the target method that would be tested.
     */
    String signature() default "";
}
