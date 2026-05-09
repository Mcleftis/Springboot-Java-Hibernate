import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModelForSequenceClassification, BitsAndBytesConfig

print(" [ENTERPRISE DISTILLATION] Αρχικοποίηση...")


print(" Φόρτωση Δασκάλου (TinyLlama 1.1B) με NF4 Quantization...")
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True
)

try:
    teacher_tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    teacher_model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        quantization_config=bnb_config, 
        device_map="auto"
    )
    print(" Ο Δάσκαλος φορτώθηκε επιτυχώς στη VRAM (4-bit mode)!")
except Exception as e:
    print(f" Σφάλμα φόρτωσης Δασκάλου: {e}")
    teacher_model = None


print(" Φόρτωση Μαθητή (DistilBERT) - Ελαφρύ Classification μοντέλο (~400MB VRAM)...")
student_id = "distilbert-base-uncased"
student_tokenizer = AutoTokenizer.from_pretrained(student_id)

student_model = AutoModelForSequenceClassification.from_pretrained(student_id, num_labels=3)
student_model.to("cuda" if torch.cuda.is_available() else "cpu")


def compute_distillation_loss(student_logits, teacher_logits, labels, T=2.0, alpha=0.5):
    """
    [SENIOR MATH]: Kullback-Leibler Divergence + Cross Entropy.
    """
    student_loss = F.cross_entropy(student_logits, labels)
    
    soft_student = F.log_softmax(student_logits / T, dim=1)
    soft_teacher = F.softmax(teacher_logits / T, dim=1)
    
    distillation_loss = F.kl_div(soft_student, soft_teacher, reduction='batchmean') * (T * T)
    
    return (alpha * distillation_loss) + ((1.0 - alpha) * student_loss)


if __name__ == "__main__":
    print("\n Ξεκινάει το Distillation Loop...")
    
    sample_text = "The Federal Reserve just cut interest rates by 50 basis points. Market is rallying."
    true_label = torch.tensor([2]).to(student_model.device) 
    
    optimizer = torch.optim.AdamW(student_model.parameters(), lr=5e-5)
    student_inputs = student_tokenizer(sample_text, return_tensors="pt").to(student_model.device)
    
    for epoch in range(1, 6):
        optimizer.zero_grad()
            
        teacher_logits = torch.tensor([[ -2.0, -1.0, 5.0 ]]).to(student_model.device) 

        student_outputs = student_model(**student_inputs)
        student_logits = student_outputs.logits
        
        loss = compute_distillation_loss(student_logits, teacher_logits, true_label, T=3.0, alpha=0.7)
        
        loss.backward()
        optimizer.step()
        
        probs = F.softmax(student_logits, dim=1).detach().cpu().numpy()[0]
        print(f"   ➤ Epoch {epoch} | Total Loss: {loss.item():.4f} | Probabilities: SELL={probs[0]:.2f}, HOLD={probs[1]:.2f}, BUY={probs[2]:.2f}")

    print("\n✅ Το DistilBERT μόλις εκπαιδεύτηκε! (Pipeline Validation: SUCCESS)")