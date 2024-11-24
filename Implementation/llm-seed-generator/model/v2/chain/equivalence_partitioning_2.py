import re
import logging

from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    FewShotChatMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.chains import LLMChain
from langchain.schema import LLMResult

SYSTEM_MESSAGE = """
You are an experienced tester. Now you are expected to partition the equivalence classes of the test inputs for the provided API method.
This API method calls more methods. 
In each class, your answer should start with "- class:" and specify the form of each parameter.
"""

QUESTION_MESSAGE = [
    ("human", "API Method: ```java {code}``` \nInvoked Methods: ```java {invoke} ```"),
    ("ai", "Answer: Let's do this step by step. "),
]

EXAMPLE_MESSAGE = [
    ("human", "API Method: ```java {code}``` \nInvoked Methods: ```java {invoke} ```"),
    ("ai", "Answer: Let's do this step by step. {answer}"),
]

EXAMPLES = [
    {
        "code": """
double valueToJava2D(double value, Rectangle2D plotArea,
                            RectangleEdge edge) {

    Range range = getRange();
    double axisMin = switchedLog10(range.getLowerBound());
    double axisMax = switchedLog10(range.getUpperBound());

    double min = 0.0;
    double max = 0.0;
    if (RectangleEdge.isTopOrBottom(edge)) {
        min = plotArea.getMinX();
        max = plotArea.getMaxX();
    }
    else if (RectangleEdge.isLeftOrRight(edge)) {
        min = plotArea.getMaxY();
        max = plotArea.getMinY();
    }

    value = switchedLog10(value);

    if (isInverted()) {
        return max - (((value - axisMin) / (axisMax - axisMin))
                * (max - min));
    }
    else {
        return min + (((value - axisMin) / (axisMax - axisMin))
                * (max - min));
    }

}
""",
        "invoke": """
boolean regionMatches(final CharSequence cs, final boolean ignoreCase, final int thisStart,
        final CharSequence substring, final int start, final int length)    {
    if (cs instanceof String && substring instanceof String) {
        return ((String) cs).regionMatches(ignoreCase, thisStart, (String) substring, start, length);
    }
    int index1 = thisStart;
    int index2 = start;
    int tmpLen = length;

    // Extract these first so we detect NPEs the same as the java.lang.String version
    final int srcLen = cs.length() - thisStart;
    final int otherLen = substring.length() - start;

    // Check for invalid parameters
    if (thisStart < 0 || start < 0 || length < 0) {
        return false;
    }

    // Check that the regions are long enough
    if (srcLen < length || otherLen < length) {
        return false;
    }

    while (tmpLen-- > 0) {
        final char c1 = cs.charAt(index1++);
        final char c2 = substring.charAt(index2++);

        if (c1 == c2) {
            continue;
        }

        if (!ignoreCase) {
            return false;
        }

        // The real same check as in String.regionMatches():
        final char u1 = Character.toUpperCase(c1);
        final char u2 = Character.toUpperCase(c2);
        if (u1 != u2 && Character.toLowerCase(u1) != Character.toLowerCase(u2)) {
            return false;
        }
    }

    return true;
}
""",
        "answer": """
Based on the method signature and body, the instances of `str` and `searchStr` should be generated to test the API method.
`str` is the CharSequence to check, `searchStr` is the CharSequence to find.
To achieve high code coverage, diverse instances should be generated to reach different branches in the Method Body.
Therefore, we can partition the following equivalence classes for str` and `searchStr`:
- class:
    1. `str`: is null; 2. `searchStr`: is any str.
- class:
    1. `str`: is any str; 2. `searchStr`: is null.
- class:
    1. `str`: is any str; 2. `searchStr`: its length is more than `str`'s length.
- class:
    1. `str`: is any str; 2. `searchStr`: is part of `str`.
- class:
    1. `str`: is any str; 2. `searchStr`: its length is less than `str`'s length and is not part of `str`.
"""
    }
]


class EquivalencePartitioningDeeperChain:
    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages(EXAMPLE_MESSAGE),
            examples=EXAMPLES,
            # examples=[]
        )
        self.final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_MESSAGE),
                few_shot_prompt,
            ] + QUESTION_MESSAGE
        )

    def parse_result(self, result: LLMResult):
        text = result.generations[0][0].text
        print(text)
        return [mobj.group(1).strip() for mobj in re.finditer(r"^- class:\n(.*)", text, re.M)]

    def run(self, code, invoke):
        messages = self.final_prompt.format_messages(code=code, invoke=invoke)
        for message in messages:
            print(f"\33[32m{message.content}\033[0m\n")
        llm_result: LLMResult = self.llm.generate([messages])
        return self.parse_result(llm_result)


if __name__ == "__main__":
    from config import *

    llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.0)
    chain = EquivalencePartitioningDeeperChain(llm)

    code = """
Apcomplex sinh(Apcomplex z)
        throws ApfloatRuntimeException
    {
        if (z.imag().signum() == 0)
        {
            return ApfloatMath.sinh(z.real());
        }

        Apfloat one = new Apfloat(1, Apfloat.INFINITE, z.radix()),
                two = new Apfloat(2, Apfloat.INFINITE, z.radix());
        Apcomplex w = exp(z);

        return (w.subtract(one.divide(w))).divide(two);
    }
"""
    invoke = """
Apfloat imag()
    {
        return this.imag;
    }
    
Apfloat sinh(Apfloat x)
        throws ApfloatRuntimeException
    {
        Apfloat y = exp(x),
                one = new Apfloat(1, Apfloat.INFINITE, x.radix()),
                two = new Apfloat(2, Apfloat.INFINITE, x.radix());

        return y.subtract(one.divide(y)).divide(two);
    }

int radix()
    {
        return (real().signum() == 0 ? (imag().signum() == 0 ? real().radix() : imag().radix()) : real().radix());
    }

Apcomplex exp(Apcomplex z)
        throws ApfloatRuntimeException
    {
        if (z.imag().signum() == 0)
        {
            return ApfloatMath.exp(z.real());
        }

        int radix = z.radix();
        Apfloat one = new Apfloat(1, Apfloat.INFINITE, radix);

        long doublePrecision = ApfloatHelper.getDoublePrecision(radix);

        // If the real part of the argument is close to 0, the result is more accurate; if it's very big the result is less accurate
        if (z.real().precision() < z.real().scale() - 1)
        {
            throw new LossOfPrecisionException("Complete loss of accurate digits in real part");
        }
        // The imaginary part must be scaled to the range of -pi ... pi, which may limit the precision
        if (z.imag().precision() < z.imag().scale())
        {
            throw new LossOfPrecisionException("Complete loss of accurate digits in imaginary part");
        }
        long realPrecision = Util.ifFinite(z.real().precision(), z.real().precision() + 1 - z.real().scale()),
             imagPrecision = Util.ifFinite(z.imag().precision(), 1 + z.imag().precision() - z.imag().scale()),
             targetPrecision = Math.min(realPrecision, imagPrecision);

        if (targetPrecision == Apfloat.INFINITE)
        {
            throw new InfiniteExpansionException("Cannot calculate exponent to infinite precision");
        }
        else if (z.real().compareTo(new Apfloat((double) Long.MAX_VALUE * Math.log((double) radix), doublePrecision, radix)) >= 0)
        {
            throw new OverflowException("Overflow");
        }
        else if (z.real().compareTo(new Apfloat((double) Long.MIN_VALUE * Math.log((double) radix), doublePrecision, radix)) <= 0)
        {
            // Underflow

            return Apcomplex.ZEROS[z.radix()];
        }

        boolean negateResult = false;                           // If the final result is to be negated
        Apfloat zImag;

        if (z.imag().scale() > 0)
        {
            long piPrecision = Util.ifFinite(targetPrecision, targetPrecision + z.imag().scale());
            Apfloat pi = ApfloatMath.pi(piPrecision, radix),    // This is precalculated for initial check only
                    twoPi = pi.add(pi),
                    halfPi = pi.divide(new Apfloat(2, targetPrecision, radix));

            // Scale z so that -pi < z.imag() <= pi
            zImag = ApfloatMath.fmod(z.imag(), twoPi);
            if (zImag.compareTo(pi) > 0)
            {
                zImag = zImag.subtract(twoPi);
            }
            else if (zImag.compareTo(pi.negate()) <= 0)
            {
                zImag = zImag.add(twoPi);
            }
            // More, scale z so that -pi/2 < z.imag() <= pi/2 to avoid instability near z.imag() = +-pi
            if (zImag.compareTo(halfPi) > 0)
            {
                // exp(z - i*pi) = exp(z)/exp(i*pi) = -exp(z)
                zImag = zImag.subtract(pi);
                negateResult = true;
            }
            else if (zImag.compareTo(halfPi.negate()) <= 0)
            {
                // exp(z + i*pi) = exp(z)*exp(i*pi) = -exp(z)
                zImag = zImag.add(pi);
                negateResult = true;
            }
        }
        else
        {
            // No need to scale the imaginary part since it's small, -pi/2 < z.imag() <= pi/2
            zImag = z.imag();
        }
        z = new Apcomplex(z.real(), zImag);

        Apfloat resultReal;
        Apcomplex resultImag;

        // First handle the real part

        if (z.real().signum() == 0)
        {
            resultReal = one;
        }
        else if (z.real().scale() < -doublePrecision / 2)
        {
            // Taylor series: exp(x) = 1 + x + x^2/2 + ...

            long precision = Util.ifFinite(-z.real().scale(), -2 * z.real().scale());
            resultReal = one.precision(precision).add(z.real());
        }
        else
        {
            // Approximate starting value for iteration

            // An overflow or underflow should not occur
            long scaledRealPrecision = Math.max(0, z.real().scale()) + doublePrecision;
            Apfloat logRadix = ApfloatMath.log(new Apfloat((double) radix, scaledRealPrecision, radix)),
                    scaledReal = z.real().precision(scaledRealPrecision).divide(logRadix),
                    integerPart = scaledReal.truncate(),
                    fractionalPart = scaledReal.frac();

            resultReal = new Apfloat(Math.pow((double) radix, fractionalPart.doubleValue()), doublePrecision, radix);
            resultReal = ApfloatMath.scale(resultReal, integerPart.longValue());

            if (resultReal.signum() == 0) {
                // Underflow
                return Apcomplex.ZEROS[z.radix()];
            }
        }

        // Then handle the imaginary part

        if (zImag.signum() == 0)
        {
            // Imaginary part may have been reduced to zero e.g. if it was exactly pi
            resultImag = one;
        }
        else if (zImag.scale() < -doublePrecision / 2)
        {
            // Taylor series: exp(z) = 1 + z + z^2/2 + ...

            long precision = Util.ifFinite(-zImag.scale(), -2 * zImag.scale());
            resultImag = new Apcomplex(one.precision(precision), zImag.precision(-zImag.scale()));
        }
        else
        {
            // Approximate starting value for iteration

            double doubleImag = zImag.doubleValue();
            resultImag = new Apcomplex(new Apfloat(Math.cos(doubleImag), doublePrecision, radix),
                                       new Apfloat(Math.sin(doubleImag), doublePrecision, radix));
        }

        // Starting value is (real part starting value) * (imag part starting value)
        Apcomplex result = resultReal.multiply(resultImag);

        long precision = result.precision();    // Accuracy of initial guess

        int iterations = 0;

        // Compute total number of iterations
        for (long maxPrec = precision; maxPrec < targetPrecision; maxPrec <<= 1)
        {
            iterations++;
        }

        int precisingIteration = iterations;

        // Check where the precising iteration should be done
        for (long minPrec = precision; precisingIteration > 0; precisingIteration--, minPrec <<= 1)
        {
            if ((minPrec - Apcomplex.EXTRA_PRECISION) << precisingIteration >= targetPrecision)
            {
                break;
            }
        }

        if (iterations > 0)
        {
            // Precalculate the needed values once to the required precision
            ApfloatMath.logRadix(targetPrecision, radix);
        }

        z = ApfloatHelper.extendPrecision(z);

        // Newton's iteration
        while (iterations-- > 0)
        {
            precision *= 2;
            result = ApfloatHelper.setPrecision(result, Math.min(precision, targetPrecision));

            Apcomplex t = log(result);
            t = lastIterationExtendPrecision(iterations, precisingIteration, t);
            t = z.subtract(t);

            if (iterations < precisingIteration)
            {
                t = new Apcomplex(t.real().precision(precision / 2),
                                  t.imag().precision(precision / 2));
            }

            result = lastIterationExtendPrecision(iterations, precisingIteration, result);
            result = result.add(result.multiply(t));

            // Precising iteration
            if (iterations == precisingIteration)
            {
                t = log(result);
                t = lastIterationExtendPrecision(iterations, -1, t);

                result = lastIterationExtendPrecision(iterations, -1, result);
                result = result.add(result.multiply(z.subtract(t)));
            }
        }

        return ApfloatHelper.setPrecision(negateResult ? result.negate() : result, targetPrecision);
    }
    
Apcomplex subtract(Apcomplex z)
        throws ApfloatRuntimeException
    {
        return new Apcomplex(real().subtract(z.real()),
                             imag().subtract(z.imag()));
    }
    
Apfloat divide(Apfloat x)
        throws ArithmeticException, ApfloatRuntimeException
    {
        if (x.signum() == 0)
        {
            throw new ArithmeticException(signum() == 0 ? "Zero divided by zero" : "Division by zero");
        }
        else if (signum() == 0)
        {
            // 0 / x = 0
            return this;
        }
        else if (x.equals(ONE))
        {
            // x / 1 = x
            return precision(Math.min(precision(), x.precision()));
        }

        long targetPrecision = Math.min(precision(),
                                        x.precision());

        if (x.isShort())
        {
            ApfloatImpl thisImpl = getImpl(targetPrecision),
                        xImpl = x.getImpl(targetPrecision),
                        impl = thisImpl.divideShort(xImpl);

            return new Apfloat(impl);
        }
        else
        {
            Apfloat inverse = ApfloatMath.inverseRoot(x, 1, targetPrecision);
            return multiply(inverse);
        }
    }
"""
    output = chain.run(code, invoke)
    print(output)
