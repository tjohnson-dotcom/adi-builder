/* Make the REAL Streamlit dropzone look like our dashed green card */
[data-testid="stFileUploaderDropzone"]{
  border:2px dashed var(--adi-green);
  background:var(--adi-green-50);
  border-radius:14px;
  padding:14px;
}
[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzone"]{ border:none; }
[data-testid="stFileUploaderDropzone"] *{ font-family: inherit; }

/* Stronger active tab with ADI-green underline (gold accent) */
.adi-tabs label[aria-checked="true"]{
  box-shadow: 0 6px 14px rgba(36,90,52,.25), inset 0 -3px 0 #C8A85A;
}
