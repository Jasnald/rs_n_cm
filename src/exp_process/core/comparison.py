from importations import *
from ..core.operations import ModelOps
from ..utils.io import IOUtils

class ComparisonPipeline:
    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.io = IOUtils()

    def compute_average(self, pattern: str, output_name: str):
        """Loads models matching a pattern (e.g., 'Side1') and saves the average."""
        models = []
        
        for fname in os.listdir(self.working_dir):
            if pattern not in fname: continue
            
            if not fname.endswith('.json'): continue
                
            if 'Average' in fname: continue

            full_path = os.path.join(self.working_dir, fname)
            data = self.io.load_json(full_path)

            if not data: continue

            models.append(data)

        if not models:
            print(f"No models found for pattern: {pattern}")
            return None

        # 2. Compute average via core logic
        avg_model = ModelOps.average_models(models)
        
        # 3. Save result
        save_path = os.path.join(self.working_dir, f"{output_name}.json")
        self.io.save_json(avg_model, save_path)
        print(f"Saved average: {output_name}")
        return avg_model

    def compute_subtraction(self, target_name: str, reference_name: str, output_name: str):
        """Subtracts reference from target (Target - Reference)."""
        
        p_target = os.path.join(self.working_dir, f"{target_name}.json")
        p_ref = os.path.join(self.working_dir, f"{reference_name}.json")
        
        m_target = self.io.load_json(p_target)
        m_ref = self.io.load_json(p_ref)

        if not m_target or not m_ref:
            print("Could not load models for subtraction.")
            return None

        diff_model = ModelOps.subtract_coeffs(m_target, m_ref)

        save_path = os.path.join(self.working_dir, f"{output_name}.json")
        self.io.save_json(diff_model, save_path)
        print(f"Saved subtraction: {output_name}")
        return diff_model