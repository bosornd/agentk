class SimpleExprEvaluator {
  final Map<String, dynamic> _state;
  SimpleExprEvaluator(this._state);

  dynamic eval(String expr) {
    // 지원: +, -, *, /, &&, ||, !, 괄호, 변수, 숫자
    // 예: "count + 1", "a && b", "!flag", "(a + b) * 2"
    // 1. 변수 치환 (a.b.c는 지원 안함, 단일 변수만)
    String replaced = expr.replaceAllMapped(RegExp(r'([a-zA-Z_][\w]*)'), (m) {
      final key = m.group(1)!;
      final val = _resolve(key);
      if (val is String) {
        // 숫자 변환 시도
        final n = num.tryParse(val);
        return n?.toString() ?? val;
      }
      return val.toString();
    });
    try {
      // 논리 연산자를 산술 연산자보다 먼저 처리
      if (replaced.contains('&&')) {
        final parts = replaced.split('&&');
        return _toBool(parts[0]) && _toBool(parts[1]);
      }
      if (replaced.contains('||')) {
        final parts = replaced.split('||');
        return _toBool(parts[0]) || _toBool(parts[1]);
      }
      if (replaced.trim().startsWith('!')) {
        return !_toBool(replaced.trim().substring(1));
      }
      // int
      if (RegExp(r'^-?\d+?$').hasMatch(replaced.trim())) {
        return int.parse(replaced.trim());
      }
      // double
      if (RegExp(r'^-?\d*\.\d+?$').hasMatch(replaced.trim())) {
        return double.parse(replaced.trim());
      }
      if (replaced.contains('+')) {
        final parts = replaced.split('+');
        return _toNum(parts[0]) + _toNum(parts[1]);
      }
      if (replaced.contains('-')) {
        final parts = replaced.split('-');
        return _toNum(parts[0]) - _toNum(parts[1]);
      }
      if (replaced.contains('*')) {
        final parts = replaced.split('*');
        return _toNum(parts[0]) * _toNum(parts[1]);
      }
      if (replaced.contains('/')) {
        final parts = replaced.split('/');
        return _toNum(parts[0]) / _toNum(parts[1]);
      }
      return replaced.trim();
    } catch (e) {
      return null;
    }
  }

  dynamic _resolve(String key) {
    if (_state.containsKey(key)) return _state[key];
    return 0;
  }

  num _toNum(String s) {
    s = s.trim();
    if (s.startsWith('"') && s.endsWith('"')) {
      s = s.substring(1, s.length - 1);
    }
    return num.tryParse(s) ?? 0;
  }

  bool _toBool(String s) {
    s = s.trim();
    if (s == 'true' || s == '1') return true;
    if (s == 'false' || s == '0') return false;
    if (_state.containsKey(s)) {
      final v = _state[s];
      if (v is bool) return v;
      if (v is num) return v != 0;
      if (v is String) return v.isNotEmpty;
    }
    // _state에 없으면, 값 자체가 비어있지 않으면 true
    return s.isNotEmpty;
  }
}
