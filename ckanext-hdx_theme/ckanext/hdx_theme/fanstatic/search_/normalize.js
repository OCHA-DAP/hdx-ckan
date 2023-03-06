//Replace accent characters
function toNormalForm(str) {
  if (typeof str !== "string")
    return str;
  return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}
