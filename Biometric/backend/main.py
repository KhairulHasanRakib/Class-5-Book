from fastapi import FastAPI, UploadFile, File, Form
kp_q, desc_q = extract_descriptors(gray_q)
if desc_q is None or len(desc_q) == 0:
return JSONResponse({"ok": False, "message": "Could not extract features from query."}, status_code=400)


# Search DB
results = []
for fp in session.query(Fingerprint).all():
desc_db = np.load(fp.descriptor_path)
score = match_score(desc_q, desc_db)
results.append({
"uid": fp.uid,
"name": fp.name,
"notes": fp.notes,
"image_path": fp.image_path,
"score": score,
})
results.sort(key=lambda x: x["score"], reverse=True)


best = results[0] if results else None
matched = bool(best and best["score"] >= threshold)


if matched:
return {"ok": True, "matched": True, "best": best, "candidates": results[:10]}
else:
if enroll_if_not_found:
# Auto-enroll as new
uid = str(uuid.uuid4())
img_path = os.path.join(IMG_DIR, f"{uid}.png")
Image.fromarray(gray_q).save(img_path)
desc_path = save_descriptor(uid, desc_q)
row = Fingerprint(uid=uid, name="Unknown", notes="Auto-enrolled", image_path=img_path, descriptor_path=desc_path)
session.add(row)
session.commit()
return {"ok": True, "matched": False, "auto_enrolled": True, "uid": uid}
else:
return {"ok": True, "matched": False, "auto_enrolled": False}
finally:
session.close()




@app.get("/list")
async def list_items():
session = SessionLocal()
try:
items = []
for fp in session.query(Fingerprint).all():
items.append({
"uid": fp.uid,
"name": fp.name,
"notes": fp.notes,
"image_path": fp.image_path
})
return {"ok": True, "items": items}
finally:
session.close()




# Serve saved images for convenience
app.mount("/files", StaticFiles(directory=DATA_DIR), name="files")