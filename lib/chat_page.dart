import 'package:flutter/material.dart';

import 'main.dart'; // ChatMessage 사용
import 'config.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatPage extends StatefulWidget {
  final String sessionName;
  final String sessionId;
  final List<ChatMessage> initialMessages;
  // 추가: 세션 상태 복원용 파라미터
  final Map<String, dynamic>? savedState;
  final dynamic savedInfoWindow;
  final Map<String, dynamic>? savedWindow;

  const ChatPage({
    super.key,
    required this.sessionName,
    required this.sessionId,
    required this.initialMessages,
    this.savedState,
    this.savedInfoWindow,
    this.savedWindow,
  });

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  // Dropdown state: {cardId: {dropdownIndex: selectedValue}}
  final Map<String, Map<int, String?>> _dropdownSelections = {};

  // 정보 윈도우에 표시할 데이터 (window 키워드 사용)
  dynamic _infoWindow;

  // 상태 변수 맵 (예: name 등)
  final Map<String, dynamic> _appState = {};

  // 서버에서 받은 최신 카드/윈도우 상태
  Map<String, dynamic>? _latestWindow;
  final Map<String, Map<String, dynamic>> _latestCards = {};

  // 카드/윈도우 위젯 생성 (window, card 모두 지원)
  Widget _buildCardOrWindowWidget(Map<String, dynamic> data) {
    final widgets = data['widgets'] as List<dynamic>?;
    final cardId = data['id'] as String?;
    if (widgets == null) return const SizedBox();
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: _buildWidgetList(widgets, cardId: cardId),
      ),
    );
  }

  // 임의 깊이의 배열/맵 경로를 재귀적으로 파싱하여 변수 치환
  String _interpolateText(String text) {
    return text.replaceAllMapped(RegExp(r'\{([^\{\}]+)\}'), (match) {
      final expr = match.group(1)!.replaceAll(' ', '');
      try {
        dynamic value = _appState;
        value = _resolvePath(value, expr);
        return value?.toString() ?? '';
      } catch (_) {
        return '';
      }
    });
  }

  // "a[0].b.c[selected].d.e"와 같은 경로를 재귀적으로 파싱 (selected도 변수로 지원)
  dynamic _resolvePath(dynamic root, String path) {
    if (path.isEmpty) return root;
    final reg = RegExp(r'^([a-zA-Z_]\w*)'); // 변수명
    final arrReg = RegExp(r'^\[([^\[\]]+)\]'); // [숫자] 또는 [변수]
    var rest = path;
    dynamic curr = root;

    while (rest.isNotEmpty && curr != null) {
      if (reg.hasMatch(rest)) {
        final m = reg.firstMatch(rest)!;
        final key = m.group(1)!;
        if (curr is Map && curr.containsKey(key)) {
          curr = curr[key];
        } else {
          return '';
        }
        rest = rest.substring(key.length);
      } else if (arrReg.hasMatch(rest)) {
        final m = arrReg.firstMatch(rest)!;
        var idxStr = m.group(1)!;
        int? idx;
        // 인덱스가 숫자가 아니면 상태 변수로 간주
        if (RegExp(r'^\d+$').hasMatch(idxStr)) {
          idx = int.parse(idxStr);
        } else {
          // 변수 치환 (예: selected)
          final idxVal = _appState[idxStr];
          if (idxVal is int) {
            idx = idxVal;
          } else if (idxVal is String && int.tryParse(idxVal) != null) {
            idx = int.parse(idxVal);
          } else {
            return '';
          }
        }
        if (curr is List && idx < curr.length) {
          curr = curr[idx];
        } else {
          return '';
        }
        rest = rest.substring(m.group(0)!.length);
      } else if (rest.startsWith('.')) {
        rest = rest.substring(1);
      } else {
        // 예기치 않은 형식
        return '';
      }
    }
    return curr;
  }

  // 위젯 리스트 빌더
  Widget _buildWidgetList(List<dynamic> widgets, {String? cardId}) {
    if (widgets.length == 1 &&
        (widgets[0]['type'] == 'column' || widgets[0]['type'] == 'row')) {
      return _buildWidgetFromJson(widgets[0], cardId: cardId, dropdownIndex: 0);
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (int i = 0; i < widgets.length; i++)
          _buildWidgetFromJson(widgets[i], cardId: cardId, dropdownIndex: i),
      ],
    );
  }

  // 재귀 위젯 빌더
  Widget _buildWidgetFromJson(
    Map<String, dynamic> w, {
    String? cardId,
    int dropdownIndex = 0,
  }) {
    switch (w['type']) {
      case 'text':
        final style = w['style'] as Map<String, dynamic>?;
        double? fontSize = style != null && style['fontSize'] != null
            ? (style['fontSize'] as num).toDouble()
            : null;
        Color? color = style != null && style['color'] != null
            ? _parseColor(style['color'])
            : null;
        FontWeight? fontWeight = style != null && style['fontWeight'] == 'bold'
            ? FontWeight.bold
            : null;
        // 변수 치환 적용
        final rawText = w['value'] ?? '';
        final text = _interpolateText(rawText);
        return Text(
          text,
          style: TextStyle(
            fontSize: fontSize,
            color: color,
            fontWeight: fontWeight,
          ),
        );
      case 'button':
        return ElevatedButton(
          onPressed: () {
            final action = w['action'] as String?;
            if (action != null && action.isNotEmpty) {
              _sendMessage(action);
            }
          },
          child: Text(w['text'] ?? ''),
        );
      case 'dropdown':
        final items = w['items'] as List<dynamic>?;
        if (items == null || items.isEmpty) return const SizedBox();
        final hint = w['hint'] as String?;
        String? selected;
        if (cardId != null) {
          _dropdownSelections.putIfAbsent(cardId, () => {});
          selected = _dropdownSelections[cardId]![dropdownIndex];
        }
        return DropdownButton<String>(
          value: selected,
          hint: hint != null ? Text(hint) : null,
          items: items
              .map<DropdownMenuItem<String>>(
                (item) => DropdownMenuItem<String>(
                  value: item,
                  child: Text(item.toString()),
                ),
              )
              .toList(),
          onChanged: (value) {
            setState(() {
              if (cardId != null) {
                _dropdownSelections[cardId]![dropdownIndex] = value;
              }
            });
          },
        );
      // --- dropbox 지원 추가 ---
      case 'dropbox':
        final items = w['items'] as List<dynamic>? ?? [];
        final label = w['label'] as String? ?? '';
        String? selected = w['selected']?.toString();
        if (cardId != null) {
          _dropdownSelections.putIfAbsent(cardId, () => {});
          selected = _dropdownSelections[cardId]![dropdownIndex] ?? selected;
        }
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (label.isNotEmpty) Text(label),
            DropdownButton<String>(
              value: selected,
              items: items
                  .map<DropdownMenuItem<String>>(
                    (item) => DropdownMenuItem<String>(
                      value: item,
                      child: Text(item.toString()),
                    ),
                  )
                  .toList(),
              onChanged: (value) {
                setState(() {
                  if (cardId != null) {
                    _dropdownSelections[cardId]![dropdownIndex] = value;
                  }
                });
              },
            ),
          ],
        );
      case 'row':
        final children = w['children'] as List<dynamic>?;
        if (children == null) return const SizedBox();
        return Row(
          mainAxisAlignment: _parseMainAxisAlignment(w['mainAxisAlignment']),
          crossAxisAlignment: _parseCrossAxisAlignment(w['crossAxisAlignment']),
          children: children
              .map<Widget>(
                (c) => Expanded(child: _buildWidgetFromJson(c, cardId: cardId)),
              )
              .toList(),
        );
      case 'column':
        final children = w['children'] as List<dynamic>?;
        if (children == null) return const SizedBox();
        return Column(
          mainAxisAlignment: _parseMainAxisAlignment(w['mainAxisAlignment']),
          crossAxisAlignment: _parseCrossAxisAlignment(w['crossAxisAlignment']),
          mainAxisSize: MainAxisSize.max,
          children: children
              .map<Widget>((c) => _buildWidgetFromJson(c, cardId: cardId))
              .toList(),
        );
      // --- text_input 지원 추가 ---
      case 'text_input':
        final label = w['label'] as String? ?? '';
        final varName = w['var'] as String?; // 상태 변수명
        final initialValue = varName != null && _appState[varName] != null
            ? _appState[varName].toString()
            : '';
        final controller = TextEditingController(text: initialValue);
        return Row(
          children: [
            if (label.isNotEmpty) Text(label),
            Expanded(
              child: TextField(
                controller: controller,
                onChanged: (value) {
                  if (varName != null) {
                    setState(() {
                      _appState[varName] = value;
                    });
                  }
                },
                decoration: InputDecoration(
                  hintText: w['hint'] as String? ?? '',
                ),
              ),
            ),
          ],
        );
      default:
        return const SizedBox();
    }
  }

  MainAxisAlignment _parseMainAxisAlignment(dynamic value) {
    switch (value) {
      case 'center':
        return MainAxisAlignment.center;
      case 'end':
        return MainAxisAlignment.end;
      case 'spaceBetween':
        return MainAxisAlignment.spaceBetween;
      case 'spaceAround':
        return MainAxisAlignment.spaceAround;
      case 'spaceEvenly':
        return MainAxisAlignment.spaceEvenly;
      case 'start':
      default:
        return MainAxisAlignment.start;
    }
  }

  CrossAxisAlignment _parseCrossAxisAlignment(dynamic value) {
    switch (value) {
      case 'center':
        return CrossAxisAlignment.center;
      case 'end':
        return CrossAxisAlignment.end;
      case 'stretch':
        return CrossAxisAlignment.stretch;
      case 'baseline':
        return CrossAxisAlignment.baseline;
      case 'start':
      default:
        return CrossAxisAlignment.start;
    }
  }

  Color? _parseColor(String? hex) {
    if (hex == null) return null;
    hex = hex.replaceFirst('#', '');
    if (hex.length == 6) {
      hex = 'FF$hex';
    }
    if (hex.length == 8) {
      return Color(int.parse('0x$hex'));
    }
    return null;
  }

  late List<ChatMessage> _messages;
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  StreamSubscription<String>? _streamSub;
  http.Client? _httpClient;

  @override
  void initState() {
    super.initState();
    _messages = List<ChatMessage>.from(widget.initialMessages);
    _httpClient = http.Client();

    // 세션 복원: 전달받은 상태가 있으면 복원
    if (widget.savedState != null) {
      _appState.addAll(widget.savedState!);
    }
    if (widget.savedInfoWindow != null) {
      _infoWindow = widget.savedInfoWindow;
    }
    if (widget.savedWindow != null) {
      _latestWindow = widget.savedWindow;
    }

    _startAgentStream();
  }

  void _startAgentStream() async {
    final url = Uri.parse('${AppConfig.serverUrl}/stream/${widget.sessionId}');
    final request = http.Request('GET', url);
    final response = await _httpClient!.send(request);
    _streamSub = response.stream
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen((line) {
          final msg = line.trim();
          if (msg.isNotEmpty) {
            debugPrint('[Agent Stream] Received: $msg');
            ChatMessage? chatMsg;
            String? cardId;
            Map<String, dynamic>? card;
            bool isWindowMsg = false;
            bool isStateMsg = false;
            try {
              final parsed = json.decode(msg);
              debugPrint('[Agent Stream] Parsed: $parsed');
              // 상태(state) 메시지 처리
              if (parsed is Map && parsed.containsKey('state')) {
                final state = parsed['state'];
                if (state is Map<String, dynamic>) {
                  setState(() {
                    _appState.addAll(state);
                  });
                  isStateMsg = true;
                }
              }
              // window 키워드가 있으면 정보 윈도우로 사용
              if (!isStateMsg &&
                  parsed is Map &&
                  parsed.containsKey('window')) {
                final window = parsed['window'];
                if (window is Map<String, dynamic>) {
                  // 변수 초기화: window 내 모든 text 위젯의 {var}를 찾아 _appState에 없으면 ""로
                  _initializeVarsFromWidgets(window['widgets']);
                  final windowId = window['id'] as String?;
                  if (windowId != null) {
                    _dropdownSelections.remove(windowId);
                  }
                  setState(() {
                    _infoWindow = window;
                    _latestWindow = window;
                  });
                  isWindowMsg = true;
                }
              }
              if (!isStateMsg && !isWindowMsg) {
                if (parsed is Map && parsed.containsKey('card')) {
                  card = parsed['card'] as Map<String, dynamic>;
                  // 변수 초기화: card 내 모든 text 위젯의 {var}를 찾아 _appState에 없으면 ""로
                  _initializeVarsFromWidgets(card['widgets']);
                  cardId = card['id'] as String?;
                  chatMsg = ChatMessage(text: '', isUser: false, card: card);
                  if (cardId != null) {
                    _latestCards[cardId] = card;
                  }
                } else {
                  chatMsg = ChatMessage(text: msg, isUser: false);
                }
              }
            } catch (e) {
              debugPrint('[Agent Stream] JSON decode error: $e');
              chatMsg = ChatMessage(text: msg, isUser: false);
            }
            if (!isStateMsg && !isWindowMsg && chatMsg != null) {
              setState(() {
                if (cardId != null) {
                  final idx = _messages.indexWhere(
                    (m) => m.card != null && m.card?['id'] == cardId,
                  );
                  if (idx != -1) {
                    _messages[idx] = chatMsg!;
                  } else {
                    _messages.add(chatMsg!);
                  }
                } else {
                  _messages.add(chatMsg!);
                }
              });
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (_scrollController.hasClients) {
                  _scrollController.jumpTo(
                    _scrollController.position.maxScrollExtent,
                  );
                  _scrollController.animateTo(
                    _scrollController.position.maxScrollExtent,
                    duration: const Duration(milliseconds: 200),
                    curve: Curves.easeOut,
                  );
                }
              });
            }
          }
        });
  }

  // card/window 내 text 위젯의 {var} 패턴을 찾아 _appState에 없으면 null로 초기화
  void _initializeVarsFromWidgets(dynamic widgets) {
    if (widgets is List) {
      for (final w in widgets) {
        _initializeVarsFromWidgets(w);
      }
    } else if (widgets is Map<String, dynamic>) {
      if (widgets['type'] == 'text' && widgets['value'] is String) {
        final matches = RegExp(r'\{(\w+)\}').allMatches(widgets['value']);
        for (final m in matches) {
          final varName = m.group(1);
          if (varName != null && !_appState.containsKey(varName)) {
            _appState[varName] = null;
          }
        }
      }
      // 재귀적으로 children/widgets도 검사
      if (widgets['children'] != null) {
        _initializeVarsFromWidgets(widgets['children']);
      }
      if (widgets['widgets'] != null) {
        _initializeVarsFromWidgets(widgets['widgets']);
      }
    }
  }

  // window/card 데이터용 빌더 (공통)
  Widget _buildWindowWidget(dynamic window) {
    if (window is Map<String, dynamic> && window.containsKey('widgets')) {
      final cardId = window['id'] as String?;
      if (cardId != null && !_dropdownSelections.containsKey(cardId)) {
        _dropdownSelections[cardId] = {};
      }
      // 항상 최신 상태(window)로 렌더링
      return _buildCardOrWindowWidget(_latestWindow ?? window);
    }
    return Text(window.toString());
  }

  Future<void> _sendMessage([String? message]) async {
    final text = message ?? _controller.text;
    if (text.trim().isEmpty) return;
    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true));
    });
    _controller.clear();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.jumpTo(_scrollController.position.maxScrollExtent);
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
    try {
      await http.post(
        Uri.parse('${AppConfig.serverUrl}/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'session_id': widget.sessionId, 'text': text}),
      );
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(text: '[에이전트 연결 오류]', isUser: false));
      });
    }
  }

  @override
  void dispose() {
    _streamSub?.cancel();
    _httpClient?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      child: Scaffold(
        appBar: AppBar(
          title: Text(widget.sessionName),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () {
              // 세션 상태를 pop으로 전달
              Navigator.of(context).pop({
                'messages': _messages,
                'state': Map<String, dynamic>.from(_appState),
                'infoWindow': _infoWindow,
                'window': _latestWindow,
              });
            },
          ),
        ),
        body: Column(
          children: [
            // 정보 윈도우: window 데이터가 있으면 상단에 표시
            if (_infoWindow != null)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.fromLTRB(8, 8, 8, 0),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.yellow[100],
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.amber, width: 1),
                ),
                child: _buildWindowWidget(_infoWindow),
              ),
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.all(8),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  final msg = _messages[index];
                  final icon = msg.isUser
                      ? const Icon(Icons.person, color: Colors.blue)
                      : const Icon(Icons.smart_toy, color: Colors.deepPurple);
                  Widget content;
                  if (msg.card != null) {
                    // Render card message (항상 최신 상태로)
                    final cardId = msg.card?['id'] as String?;
                    final cardData =
                        cardId != null && _latestCards.containsKey(cardId)
                        ? _latestCards[cardId]!
                        : msg.card!;
                    content = _buildCardOrWindowWidget(cardData);
                  } else {
                    content = Text(msg.text);
                  }
                  return Align(
                    alignment: msg.isUser
                        ? Alignment.centerRight
                        : Alignment.centerLeft,
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: msg.isUser
                          ? [
                              Flexible(
                                child: Container(
                                  margin: const EdgeInsets.symmetric(
                                    vertical: 2,
                                    horizontal: 4,
                                  ),
                                  padding: const EdgeInsets.symmetric(
                                    vertical: 8,
                                    horizontal: 12,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.blue[100],
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: content,
                                ),
                              ),
                              icon,
                            ]
                          : [
                              icon,
                              Flexible(
                                child: Container(
                                  margin: const EdgeInsets.symmetric(
                                    vertical: 2,
                                    horizontal: 4,
                                  ),
                                  padding: const EdgeInsets.symmetric(
                                    vertical: 8,
                                    horizontal: 12,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.grey[300],
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: content,
                                ),
                              ),
                            ],
                    ),
                  );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      onSubmitted: (value) => _sendMessage(value),
                      decoration: const InputDecoration(
                        hintText: '메시지를 입력하세요...',
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.send),
                    onPressed: _sendMessage,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
