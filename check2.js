const fs = require('fs');

const data = JSON.parse(fs.readFileSync('C:\Users\sixth\Downloads\호흡기 2차\output\questions_mapping.json', 'utf8'));

const questions = Array.isArray(data) ? data : (data.questions || Object.values(data));

function filterQuestions(topicKeyword) {
  return questions.filter(q => {
    const topic = q.topic || '';
    const session = q.session || '';
    const year = parseInt(q.year) || 0;
    return topic.includes(topicKeyword) && session !== '차시14' && year >= 2020;
  });
}

const categories = [
  { label: '환기장애', keyword: '환기장애' },
  { label: '수면무호흡', keyword: '수면무호흡' },
  { label: '폐색전증', keyword: '폐색전증' },
];

let output = '';

for (const cat of categories) {
  const results = filterQuestions(cat.keyword);
  output += `\n========== [${cat.label}] (session != 차시14, year >= 2020) ==========\n`;
  output += `총 ${results.length}개 문항\n`;
  if (results.length > 0) {
    results.forEach((q, i) => {
      output += `\n[${i + 1}] year: ${q.year}, session: ${q.session}, topic: ${q.topic}\n`;
      output += `     id: ${q.id || q.question_id || '(없음)'}\n`;
      const text = (q.question || q.text || '').replace(/\n/g, ' ').slice(0, 100);
      output += `     문제: ${text}\n`;
    });
  }
}

fs.writeFileSync('C:\Users\sixth\Downloads\호흡기 2차\check2_output.txt', output, 'utf8');
process.stdout.write(output);
