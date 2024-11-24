package edu.berkeley.cs.jqf.instrument;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Objects;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class InstructionClass {
    private int iid;
    private int taken;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        InstructionClass that = (InstructionClass) o;
        return iid == that.iid && taken == that.taken;
    }

    @Override
    public int hashCode() {
        return Objects.hash(iid, taken);
    }
}
