import base64

async def encode_f_to_cq(path:str, f_type: str, other_args = ""):
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
        cq_code = f"[CQ:{f_type},file=base64://{encoded}"
        if len(other_args) > 0:
            cq_code += "," + other_args

        cq_code += "]"
        return cq_code