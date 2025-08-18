import threading
import os
import platform
import subprocess
from datetime import datetime
from tkinter import filedialog, messagebox
from utils.utils import VideoUtils, show_custom_messagebox
from utils.extract.image_extractor import ImageUtils
from utils.event_system import event_system, Events
from utils.extract.video_extractor import VideoExtractor, ExtractConfig
from utils.extract.image_extractor import ImageExtractor
from utils.extract.audio_extractor import AudioExtractor


class ExtractionManager:
    """추출 작업 관리자"""

    def __init__(self, parent_frame, app, ffmpeg_manager=None):
        self.parent_frame = parent_frame
        self.app = app
        self.ffmpeg_manager = ffmpeg_manager

        # 작업 상태 플래그
        self._is_extracting = False
        self._is_image_extracting = False
        self._is_audio_extracting = False

        # 취소 이벤트
        self.cancel_event = threading.Event()

        # 추출 설정
        self.extract_config = ExtractConfig()

    def is_busy(self):
        """작업 중인지 확인"""
        return (self._is_extracting or
                self._is_image_extracting or
                self._is_audio_extracting)

    def cancel_all_extractions(self):
        """모든 추출 작업 취소"""
        self.cancel_event.set()  # 취소 신호 전송
        self._is_extracting = False
        self._is_image_extracting = False
        self._is_audio_extracting = False
        print("모든 추출 작업 취소 신호 전송됨")

        # 취소 이벤트 방송
        try:
            self._emit_extraction_cancelled()
        except Exception:
            pass

    def extract_video_segment(self, segment_info=None):
        """비디오 구간 추출"""
        try:
            # 중복 실행 방지
            if self._is_extracting:
                show_custom_messagebox(
                    self.parent_frame, "경고",
                    "이미 비디오 추출 작업이 진행 중입니다.", "warning")
                return

            # 구간 정보 가져오기
            if not segment_info:
                segment_info = self._get_selected_segment_info()
                if not segment_info:
                    return

            # FFmpeg 확인
            if self.ffmpeg_manager and not self.ffmpeg_manager.require_ffmpeg_or_show_error(self.parent_frame, "비디오"):
                return

            # 입력 파일 찾기
            input_path = self._find_input_file(segment_info)
            if not input_path:
                return

            # 출력 파일 선택
            output_path = self._get_video_output_path(segment_info)
            if not output_path:
                return

            # 추출 시작
            self._start_video_extraction(input_path, output_path, segment_info)

        except Exception as e:
            self._handle_extraction_error("비디오", e)

    def _handle_extraction_error(self, extraction_type, error):
        """추출 준비 중 에러 처리"""
        show_custom_messagebox(
            self.parent_frame, "오류",
            f"{extraction_type} 추출 준비 중 오류: {str(error)}", "error")

    def extract_images(self, segment_info=None):
        """선택한 구간에서 이미지 추출"""
        try:
            # 중복 실행 방지
            if self._is_image_extracting:
                show_custom_messagebox(
                    self.parent_frame, "경고",
                    "이미 이미지 추출 작업이 진행 중입니다.", "warning")
                return

            # 1. 선택한 구간 정보 가져오기
            if not segment_info:
                segment_info = self._get_selected_segment_info()
                if not segment_info:
                    return

            # 2. 입력 파일 찾기
            input_path = self._find_input_file(segment_info)
            if not input_path:
                return

            # 3.출력 폴더 설정
            output_folder = self._get_image_output_folder(
                input_path, segment_info)
            if not output_folder:
                return

            # 4. 이미지 추출 시작
            self._start_image_extraction(
                input_path, output_folder, segment_info)

        except Exception as e:
            self._handle_extraction_error("이미지", e)

    def extract_audio(self, segment_info=None):
        """오디오 추출"""
        try:
            # 중복 실행 방지
            if self._is_audio_extracting:
                show_custom_messagebox(
                    self.parent_frame, "경고",
                    "이미 오디오 추출 작업이 진행 중입니다.", "warning")
                return

            # 구간 정보 가져오기
            if not segment_info:
                segment_info = self._get_selected_segment_info()
                if not segment_info:
                    return

            # FFmpeg 확인 (오디오 추출에는 필수)
            if self.ffmpeg_manager and not self.ffmpeg_manager.require_ffmpeg_or_show_error(self.parent_frame, "오디오"):
                return

            # 입력 파일 찾기
            input_path = self._find_input_file(segment_info)
            if not input_path:
                return

            # 출력 폴더 설정
            output_folder = self._get_audio_output_folder(
                input_path, segment_info)
            if not output_folder:
                return

            # 추출 시작
            self._start_audio_extraction(
                input_path, output_folder, segment_info)

        except Exception as e:
            self._handle_extraction_error("오디오", e)

    def _get_selected_segment_info(self):
        """선택된 구간 정보 가져오기"""
        if not hasattr(self.app, 'saved_segments') or not self.app.saved_segments:
            show_custom_messagebox(
                self.parent_frame, "경고",
                "추출할 구간이 없습니다.\n먼저 구간을 저장해주세요.", "warning")
            return None

        # UI에서 선택된 구간 우선 반환
        try:
            if hasattr(self.app, 'new_tab_instance') and \
               hasattr(self.app.new_tab_instance, 'segment_table') and \
               hasattr(self.app.new_tab_instance.segment_table, 'table'):
                tree = self.app.new_tab_instance.segment_table.table
                selected_items = tree.selection()
                if selected_items:
                    index = tree.index(selected_items[0])
                    if 0 <= index < len(self.app.saved_segments):
                        return self.app.saved_segments[index]
        except Exception:
            # 선택 정보 조회 실패 시 최신 구간으로 폴백
            pass

        # 선택이 없거나 에러 시 최신 구간 반환
        return self.app.saved_segments[-1]

    def _find_input_file(self, segment_info):
        """입력 파일 찾기"""
        input_path = VideoUtils.find_input_file(segment_info['file'], self.app)
        if not input_path or not os.path.exists(input_path):
            # 사용자가 직접 파일 선택
            response = messagebox.askyesno(
                "파일 없음",
                "원본 비디오 파일을 찾을 수 없습니다.\n직접 선택하시겠습니까?"
            )

            if response:
                input_path = filedialog.askopenfilename(
                    title="원본 비디오 파일 선택",
                    filetypes=VideoExtractor.get_supported_formats()
                )
                return input_path if input_path else None
            else:
                return None

        return input_path

    def _get_video_output_path(self, segment_info):
        """비디오 출력 파일 경로 설정"""
        default_filename = self.extract_config.generate_filename(segment_info)

        output_path = filedialog.asksaveasfilename(
            title="비디오 저장할 위치 선택",
            defaultextension=".mp4",
            filetypes=VideoExtractor.get_supported_formats(),
            initialfile=default_filename
        )

        return output_path if output_path else None

    def _get_image_output_folder(self, input_path, segment_info):
        """이미지 출력 폴더 설정"""
        folder_name = ImageUtils.generate_output_folder_name(
            input_path, segment_info['start'], segment_info['end'])

        default_path = VideoUtils.get_default_save_path()

        output_base_folder = filedialog.askdirectory(
            title="이미지 저장할 기본 폴더 선택",
            initialdir=default_path
        )
        if not output_base_folder:
            output_base_folder = default_path

        output_folder = os.path.join(output_base_folder, folder_name)

        # 폴더 생성
        if not self._create_output_folder(output_folder, folder_name):
            return None

        return output_folder

    def _get_audio_output_folder(self, input_path, segment_info):
        """오디오 출력 폴더 설정"""
        # 이미지와 동일한 방식 사용
        return self._get_image_output_folder(input_path, segment_info)

    def _create_output_folder(self, output_folder, folder_name):
        """출력 폴더 생성"""
        if os.path.exists(output_folder):
            response = messagebox.askyesno(
                "폴더 존재",
                f"폴더 '{folder_name}'이 이미 존재합니다.\n기존 폴더에 추가하시겠습니까?"
            )
            if not response:
                return False
        else:
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                show_custom_messagebox(
                    self.parent_frame, "오류",
                    f"폴더 생성 실패: {str(e)}", "error")
                return False
        return True

    def _start_video_extraction(self, input_path, output_path, segment_info):
        """비디오 추출 시작"""
        self._is_extracting = True
        self.cancel_event.clear()

        print(f"비디오 추출 시작: {segment_info['start']}~{segment_info['end']}초")

        # 진행률 이벤트 발생
        event_system.emit(
            Events.EXTRACTION_PROGRESS,
            progress=0,
            status="비디오 추출 준비 중...",
            icon="🔄"
        )

        # 백그라운드 스레드에서 추출 실행
        threading.Thread(
            target=self._do_video_extraction,
            args=(input_path, output_path, segment_info),
            daemon=True
        ).start()

    def _start_image_extraction(self, input_path, output_folder, segment_info):
        """이미지 추출 시작"""
        self._is_image_extracting = True
        self.cancel_event.clear()

        print(f"이미지 추출 시작: {segment_info['start']}~{segment_info['end']}초")
        print(f"이미지 저장 폴더: {output_folder}")

        # 진행률 이벤트 발생
        event_system.emit(
            Events.IMAGE_EXTRACTION_PROGRESS,
            progress=0,
            status="이미지 추출 준비 중...",
            icon="🔄"
        )

        # 백그라운드 스레드에서 추출 실행
        threading.Thread(
            target=self._do_image_extraction,
            args=(input_path, output_folder, segment_info),
            daemon=True
        ).start()

    def _start_audio_extraction(self, input_path, output_folder, segment_info):
        """오디오 추출 시작"""
        self._is_audio_extracting = True
        self.cancel_event.clear()

        print(f"오디오 추출 시작: {segment_info['start']}~{segment_info['end']}초")
        print(f"오디오 저장 폴더: {output_folder}")

        # 진행률 이벤트 발생
        event_system.emit(
            Events.AUDIO_EXTRACTION_PROGRESS,
            progress=0,
            status="오디오 추출 준비 중...",
            icon="🔄"
        )

        # 백그라운드 스레드에서 추출 실행
        threading.Thread(
            target=self._do_audio_extraction,
            args=(input_path, output_folder, segment_info),
            daemon=True
        ).start()

    def _do_video_extraction(self, input_path, output_path, segment_info):
        """실제 비디오 추출 작업 (백그라운드)"""
        try:
            # 취소 확인
            if self.cancel_event.is_set():
                self._emit_extraction_cancelled()
                return

            # extract/video_extractor.py 의 VideoExtractor로 추출
            result = VideoExtractor.extract_segment(
                input_video_path=input_path,
                output_video_path=output_path,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=self._video_progress_callback,
                ffmpeg_executable=self._get_ffmpeg_executable()
            )

            # 결과 이벤트 발생
            self.parent_frame.after(
                0, lambda: self._emit_video_extraction_complete(result))

        except Exception as e:
            self.parent_frame.after(
                0, lambda err=e: self._emit_extraction_error(str(err)))

    def _do_image_extraction(self, input_path, output_folder, segment_info):
        """실제 이미지 추출 작업 (백그라운드)"""
        try:
            # 취소 확인
            if self.cancel_event.is_set():
                self._emit_extraction_cancelled()
                return

            # 이미지 추출 시작 이벤트
            event_system.emit(
                Events.IMAGE_EXTRACTION_START,
                input_path=input_path,
                output_folder=output_folder,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                method='opencv'
            )

            # extract/ImageExtractor.py의 메서드드를 사용하여 프레임 추출
            result = ImageExtractor.extract_frames_from_video(
                input_path=input_path,
                output_folder=output_folder,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=self._image_progress_callback,
                cancel_event=self.cancel_event
            )

            # OpenCV가 실패하거나 0개 추출 시 FFmpeg 폴백 시도
            if (not result) or (result.get('extracted_count', 0) == 0):
                print("OpenCV 이미지 추출 결과가 0개입니다. FFmpeg 폴백(이미지 추출)을 시도합니다.")

                # FFmpeg 폴백 시작 이벤트
                event_system.emit(
                    Events.IMAGE_EXTRACTION_START,
                    input_path=input_path,
                    output_folder=output_folder,
                    start_time=segment_info['start'],
                    end_time=segment_info['end'],
                    method='ffmpeg_fallback'
                )

                ff_result = ImageExtractor.extract_frames_with_ffmpeg(
                    input_path=input_path,
                    output_folder=output_folder,
                    start_time=segment_info['start'],
                    end_time=segment_info['end'],
                    ffmpeg_executable=self._get_ffmpeg_executable()
                )
                if ff_result.get('success') and ff_result.get('extracted_count', 0) > 0:
                    # 폴백 성공 시 결과 변환하여 동일 경로로 전달
                    result = {
                        'extracted_count': ff_result.get('extracted_count', 0),
                        'total_frames': ff_result.get('extracted_count', 0),
                        'fps': 0,
                        'frame_skip': 0
                    }
                else:
                    # 폴백 실패 시 에러 이벤트
                    error_msg = ff_result.get('message', 'FFmpeg 폴백 실패')
                    self._handle_image_extraction_error(error_msg)
                    return

            # 결과 이벤트 발생
            self.parent_frame.after(
                0, lambda: self._emit_image_extraction_complete(result, output_folder))

        except Exception as e:
            error_msg = f"이미지 추출 중 오류 발생: {str(e)}"
            self._handle_image_extraction_error(error_msg)

    def _handle_image_extraction_error(self, error_msg):
        """이미지 추출 에러 처리 (이벤트 + UI)"""
        event_system.emit(Events.IMAGE_EXTRACTION_ERROR, message=error_msg)
        self.parent_frame.after(
            0, lambda: self._emit_extraction_error(error_msg))

    def _do_audio_extraction(self, input_path, output_folder, segment_info):
        """실제 오디오 추출 작업 (백그라운드)"""
        try:
            # 취소 확인
            if self.cancel_event.is_set():
                self._emit_extraction_cancelled()
                return

            # AudioExtractor를 사용하여 오디오 추출
            base_filename = os.path.splitext(os.path.basename(input_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"{base_filename}_{timestamp}.mp3"
            output_path = os.path.join(output_folder, audio_filename)

            result = AudioExtractor.extract_audio_segment(
                input_video_path=input_path,
                output_audio_path=output_path,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=self._audio_progress_callback,
                audio_format='mp3',
                audio_quality='192k',
                ffmpeg_executable=self._get_ffmpeg_executable()
            )

            # 결과 이벤트 발생
            self.parent_frame.after(
                0, lambda: self._emit_audio_extraction_complete(result, output_folder))

        except Exception as e:
            self.parent_frame.after(
                0, lambda err=e: self._emit_extraction_error(str(err)))

    def _video_progress_callback(self, message):
        """비디오 추출 진행률 콜백"""
        if not self.cancel_event.is_set():
            self.parent_frame.after(0, lambda: event_system.emit(
                Events.EXTRACTION_PROGRESS,
                progress=50,
                status=f"비디오 추출 중... {message}"))

    def _image_progress_callback(self, progress, extracted_count, total_frames):
        """이미지 추출 진행률 콜백"""
        if not self.cancel_event.is_set():
            self.parent_frame.after(0, lambda: event_system.emit(
                Events.IMAGE_EXTRACTION_PROGRESS,
                progress=progress,
                status=f"이미지 {extracted_count}/{total_frames} 저장 중..."
            ))

    def _audio_progress_callback(self, message="오디오 추출 중..."):
        """오디오 추출 진행률 콜백"""
        if not self.cancel_event.is_set():
            self.parent_frame.after(0, lambda: event_system.emit(
                Events.AUDIO_EXTRACTION_PROGRESS,
                progress=50,
                status=message
            ))

    def _emit_video_extraction_complete(self, result):
        """비디오 추출 완료 이벤트 발생"""
        self._is_extracting = False

        event_system.emit(
            Events.EXTRACTION_COMPLETE,
            success=result['success'],
            message=result['message'],
            output_path=result.get('output_path', ''),
            progress=100,
            status="비디오 추출 완료!"
        )

        # 사용자 알림 (완료 메시지)
        try:
            success = result.get('success', False)
            output_path = result.get('output_path', '')
            message = result.get('message', '')
            if success and output_path:
                self.parent_frame.after(0, lambda: show_custom_messagebox(
                    self.parent_frame,
                    "비디오 추출 완료",
                    f"저장 위치:\n{output_path}",
                    "success"
                ))
            elif not success:
                self.parent_frame.after(0, lambda: show_custom_messagebox(
                    self.parent_frame,
                    "비디오 추출 실패",
                    message or "알 수 없는 오류",
                    "error"
                ))
        except Exception:
            pass

    def _emit_image_extraction_complete(self, result, output_folder):
        """이미지 추출 완료 이벤트 발생"""
        self._is_image_extracting = False

        event_system.emit(
            Events.IMAGE_EXTRACTION_COMPLETE,
            extracted_count=result['extracted_count'],
            total_extract_frames=result['total_frames'],
            output_folder=output_folder,
            progress=100,
            status=f"{result['extracted_count']}개 이미지 추출 완료!"
        )

        # 사용자 알림 (완료 메시지)
        try:
            count = result.get('extracted_count', 0)
            total = result.get('total_frames', 0)
            if total == 0 or count == 0:
                # 코덱/구간 문제 등으로 저장된 이미지가 없을 때 사용자에게 안내
                self.parent_frame.after(0, lambda: show_custom_messagebox(
                    self.parent_frame,
                    "이미지 추출 결과",
                    "이미지가 저장되지 않았습니다.\n\n가능한 원인:\n- 선택한 구간에 유효한 프레임이 없음\n- OpenCV 코덱 불일치로 디코딩 실패\n\n다른 구간으로 시도하거나 영상 코덱을 변환해 보세요.",
                    "warning"
                ))
                return
            self.parent_frame.after(0, lambda: show_custom_messagebox(
                self.parent_frame,
                "이미지 추출 완료",
                f"저장 폴더:\n{output_folder}\n\n저장 개수: {count}/{total}",
                "success"
            ))
        except Exception:
            pass

    def _emit_audio_extraction_complete(self, result, output_folder):
        """오디오 추출 완료 이벤트 발생"""
        self._is_audio_extracting = False

        # 결과 확인 및 경고
        out_path = result.get('output_path') if isinstance(
            result, dict) else None
        if not out_path or not os.path.exists(out_path):
            print("⚠️ 오디오 추출 결과 파일이 확인되지 않습니다.")
            event_system.emit(
                Events.AUDIO_EXTRACTION_ERROR,
                error=result.get('message', '오디오 파일 생성 실패'),
                progress=0,
                status="오디오 파일 생성 실패")
            return

        event_system.emit(
            Events.AUDIO_EXTRACTION_COMPLETE,
            extracted_count=result.get('extracted_count', 1),
            output_folder=os.path.dirname(
                out_path) if out_path else output_folder,
            progress=100,
            status="오디오 추출 완료!"
        )

        # 사용자 알림 (완료 메시지)
        try:
            self.parent_frame.after(0, lambda: show_custom_messagebox(
                self.parent_frame,
                "오디오 추출 완료",
                f"저장 위치:\n{out_path}",
                "success"
            ))
        except Exception:
            pass

    def _emit_extraction_error(self, error_message):
        """추출 오류 이벤트 발생"""
        self._is_extracting = False
        self._is_image_extracting = False
        self._is_audio_extracting = False

        event_system.emit(
            Events.EXTRACTION_ERROR,
            error=error_message,
            progress=0,
            status="오류 발생",
            icon="⚠️"
        )

    def _emit_extraction_cancelled(self):
        """추출 취소 이벤트 발생"""
        self._is_extracting = False
        self._is_image_extracting = False
        self._is_audio_extracting = False

        event_system.emit(
            Events.EXTRACTION_CANCEL,
            progress=0,
            status="취소됨"
        )

    @staticmethod
    def open_file_location(file_path):
        """파일 위치 열기"""
        try:
            folder_path = os.path.dirname(file_path)

            if platform.system() == 'Windows':
                os.startfile(folder_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', folder_path])
            else:  # Linux
                subprocess.run(['xdg-open', folder_path])

        except Exception as e:
            print(f"폴더 열기 실패: {e}")

    def do_extraction(self, input_path, output_path, segment_info):
        """실제 추출 작업 (백그라운드)"""
        try:
            # 취소 이벤트 초기화
            self.cancel_event.clear()

            # 취소 확인 (한 번만 체크)
            if self.cancel_event.is_set():
                self.update_progress_safe(0, "취소됨", "취소")
                return

            # 시작 상태 업데이트
            self.update_progress_safe(0, "추출 시작...", "시작...")

            # VideoExtractor로 추출 (코덱 복사 옵션 제거)
            result = VideoExtractor.extract_segment(
                input_video_path=input_path,
                output_video_path=output_path,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=self.extraction_progress_callback
            )

            # 결과 표시
            self.frame.after(0, lambda: self.show_extraction_result(result))

        except Exception as e:
            # 오류 발생 시, lambda 기본 인자를 사용하여 현재의 e 값을 캡처
            self.frame.after(
                0, lambda error=e: self.show_extraction_error(error))

    def extraction_progress_callback(self, msg):
        """추출 진행률 콜백"""
        if not self.cancel_event.is_set():  # 취소되지 않은 경우만 업데이트
            self.update_progress_safe(50, f"🔄 {msg}", "⚙️")

    def show_extraction_result(self, result):
        """추출 결과 표시"""
        # 추출 완료 후 플래그 리셋
        self._is_extracting = False

        if result['success']:
            self.update_progress(100, "추출 완료!", "✅")
            messagebox.showinfo(
                "비디오 추출 완료", "추출 성공!", parent=self.frame)

        else:
            self.update_progress(0, " 추출 실패", "❌")
            show_custom_messagebox(
                self.frame, "비디오 추출 실패", f"추출 실패: {result['message']}", "error")

        # 5초 후 진행률 바 초기화
        self.frame.after(5000, lambda: self.update_progress(0, "대기 중...", "⚡"))

    def show_extraction_error(self, error):
        """추출 오류 표시"""
        # 추출 오류 후 플래그 리셋
        self._is_extracting = False

        self.update_progress(0, "오류 발생", "⚠️")
        show_custom_messagebox(
            self.frame, "오류", f"추출 중 오류: {str(error)}", "warning")

    def update_progress_safe(self, value, status="", icon="⚡", **kwargs):  # 백그라운드 작업
        """스레드 안전한 진행률 업데이트 헬퍼 메서드"""
        self.frame.after(0, lambda: self.update_progress(value, status, icon))

    def _get_ffmpeg_executable(self):
        """FFmpeg 실행 경로 가져오기"""
        return (self.ffmpeg_manager.ffmpeg_path
                if self.ffmpeg_manager and self.ffmpeg_manager.ffmpeg_path else 'ffmpeg')
