import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path = 'outputs/floyd_excel/floyd_warshall.xlsx';
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
console.log((await workbook.inspect({kind:'sheet', include:'id,name', maxChars:1200})).ndjson);
console.log((await workbook.inspect({kind:'table', range:'Iteraciones!A9:F13', include:'values', tableMaxRows:5,tableMaxCols:6,maxChars:1800})).ndjson);
for (const [sheetName,range,file] of [
  ['Iteraciones','A7:AE18','iteraciones.png'],
  ['Iteraciones','AG77:BK88','recorridos.png'],
  ['Resultado','A7:AE18','resultado.png']
].filter((_,i)=>i===Number(process.argv[2]??0))) {
 const png=await workbook.render({sheetName,range,scale:1,format:'png'});
 await fs.writeFile('tmp/excel_qa/'+file,new Uint8Array(await png.arrayBuffer()));
}
