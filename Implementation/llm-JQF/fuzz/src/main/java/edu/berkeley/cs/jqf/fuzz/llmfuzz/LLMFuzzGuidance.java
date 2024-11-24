package edu.berkeley.cs.jqf.fuzz.llmfuzz;

import edu.berkeley.cs.jqf.fuzz.guidance.Guidance;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public interface LLMFuzzGuidance extends Guidance {
    String OBJECT_STORAGE = "../.object_storage";
    Logger logger = LoggerFactory.getLogger(LLMFuzzGuidance.class);
}
